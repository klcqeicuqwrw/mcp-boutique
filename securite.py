"""Authentification, droits d'accès aux données et journal des requêtes SQL."""
import hashlib, hmac, json, os, secrets, sqlite3, time
from contextlib import closing
from pathlib import Path

APP_DB = Path(os.environ.get("APP_DB_PATH", "app.db")).expanduser().resolve()
SESSION_TTL = 12 * 3600
_echecs: dict = {}


def q(sql, args=(), one=False, write=False):
    """Exécute une requête sur la base applicative (comptes, conversations, logs)."""
    with closing(sqlite3.connect(APP_DB)) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        cur = c.execute(sql, args)
        if write:
            c.commit()
            return cur.lastrowid
        rows = [dict(r) for r in cur.fetchall()]
    return (rows[0] if rows else None) if one else rows


def init_db():
    with closing(sqlite3.connect(APP_DB)) as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS services(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS permissions(
            service_id INTEGER NOT NULL REFERENCES services(id) ON DELETE CASCADE,
            table_name TEXT NOT NULL, columns TEXT,  -- JSON ou NULL = toutes les colonnes
            PRIMARY KEY(service_id, table_name));
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, pwd_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','user')),
            service_id INTEGER REFERENCES services(id) ON DELETE SET NULL,
            active INTEGER NOT NULL DEFAULT 1, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            titre TEXT, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,
            conv_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            question TEXT, reponse TEXT, sql TEXT, resultats TEXT, erreur TEXT, created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS query_log(id INTEGER PRIMARY KEY, user_id INTEGER, username TEXT,
            question TEXT, sql TEXT, status TEXT, row_count INTEGER, duration_ms INTEGER, created_at REAL);
        """)
    if not q("SELECT 1 FROM users WHERE role='admin'", one=True):
        pwd = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
        creer_utilisateur(os.environ.get("ADMIN_USERNAME", "admin"), pwd, "admin")
        print(f"[SECURITE] Compte admin créé. Mot de passe initial : {pwd}  (à changer)")


# --- Mots de passe et sessions ------------------------------------------------

def hash_pw(p, salt=None):
    salt = salt or secrets.token_bytes(16)
    return salt.hex() + "$" + hashlib.scrypt(p.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def check_pw(p, stored):
    salt, h = stored.split("$")
    return hmac.compare_digest(hash_pw(p, bytes.fromhex(salt)).split("$")[1], h)


def creer_utilisateur(username, password, role="user", service_id=None):
    if len(password) < 10:
        raise ValueError("Le mot de passe doit contenir au moins 10 caractères.")
    return q("INSERT INTO users(username,pwd_hash,role,service_id,created_at) VALUES(?,?,?,?,?)",
             (username.strip(), hash_pw(password), role, service_id, time.time()), write=True)


def login(username, password):
    """Retourne un jeton de session ou None. Limite à 5 échecs / 5 min par compte."""
    now = time.time()
    tentatives = [t for t in _echecs.get(username, []) if now - t < 300]
    if len(tentatives) >= 5:
        raise PermissionError("Trop de tentatives. Réessayez dans quelques minutes.")
    u = q("SELECT * FROM users WHERE username=? AND active=1", (username,), one=True)
    # vérification factice si le compte n'existe pas (temps constant)
    ok = check_pw(password, u["pwd_hash"] if u else hash_pw("x"))
    if not (u and ok):
        _echecs[username] = tentatives + [now]
        return None
    _echecs.pop(username, None)
    token = secrets.token_urlsafe(32)
    q("INSERT INTO sessions VALUES(?,?,?)",
      (hashlib.sha256(token.encode()).hexdigest(), u["id"], now + SESSION_TTL), write=True)
    return token


def user_from_token(token):
    if not token:
        return None
    return q("""SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id
                WHERE s.token_hash=? AND s.expires>? AND u.active=1""",
             (hashlib.sha256(token.encode()).hexdigest(), time.time()), one=True)


def logout(token):
    q("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),), write=True)


# --- Droits d'accès aux données ------------------------------------------------

def allowed_for(user):
    """None = accès total (admin) ; sinon {table: set(colonnes) | None}."""
    if user["role"] == "admin":
        return None
    if not user["service_id"]:
        return {}
    rows = q("SELECT table_name, columns FROM permissions WHERE service_id=?", (user["service_id"],))
    return {r["table_name"].lower(): ({c.lower() for c in json.loads(r["columns"])} if r["columns"] else None)
            for r in rows}


def _authorizer(allowed):
    """Callback SQLite : refuse toute lecture hors des tables/colonnes autorisées,
    y compris via jointures, sous-requêtes, CTE ou vues."""
    def check(action, a1, a2, _db, _src):
        if action == sqlite3.SQLITE_READ:
            if a1.lower().startswith("sqlite_"):
                return sqlite3.SQLITE_DENY
            if allowed is None:
                return sqlite3.SQLITE_OK
            if a1.lower() not in allowed:
                return sqlite3.SQLITE_DENY
            cols = allowed[a1.lower()]
            return sqlite3.SQLITE_OK if (cols is None or not a2 or a2.lower() in cols) else sqlite3.SQLITE_DENY
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    return check


def tables_info():
    """{table: [colonnes]} de toute la base métier (pour l'interface admin)."""
    from api import _connect_read_only
    with closing(_connect_read_only()) as c:
        noms = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {t: [r[1] for r in c.execute(f'PRAGMA table_info("{t}")')] for t in noms}


def schema_text(allowed):
    """Schéma filtré selon les droits : c'est le seul que voit le modèle IA."""
    from api import _connect_read_only
    lignes = []
    with closing(_connect_read_only()) as c:
        for t in tables_info():
            if allowed is not None and t.lower() not in allowed:
                continue
            cols = allowed[t.lower()] if allowed is not None else None
            info = [f"{r[1]} {r[2]}" for r in c.execute(f'PRAGMA table_info("{t}")')
                    if cols is None or r[1].lower() in cols]
            ligne = f"{t}({', '.join(info)})"
            fks = [f"{r[3]}->{r[2]}.{r[4]}" for r in c.execute(f'PRAGMA foreign_key_list("{t}")')
                   if allowed is None or r[2].lower() in allowed]
            lignes.append(ligne + (" FK: " + ", ".join(fks) if fks else ""))
    return "\n".join(lignes)


def run_query(user, sql, max_rows=500):
    from api import _connect_read_only, _validate_read_query
    sql = _validate_read_query(sql)
    with closing(_connect_read_only()) as c:
        c.set_authorizer(_authorizer(allowed_for(user)))
        try:
            cur = c.execute(sql)
            cols = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(max_rows + 1)
        except sqlite3.DatabaseError as e:
            if "not authorized" in str(e):
                raise PermissionError("Accès refusé : cette requête touche des données non autorisées pour votre service.") from e
            raise RuntimeError(f"Erreur SQLite : {e}") from e
    trunc = len(rows) > max_rows
    rows = rows[:max_rows]
    return {"columns": cols, "rows": [dict(zip(cols, r)) for r in rows],
            "row_count": len(rows), "truncated": trunc}


def log_query(user, question, sql, status, rows=0, ms=0):
    q("INSERT INTO query_log(user_id,username,question,sql,status,row_count,duration_ms,created_at) "
      "VALUES(?,?,?,?,?,?,?,?)", (user["id"], user["username"], question, sql, status, rows, ms, time.time()),
      write=True)