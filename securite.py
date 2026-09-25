"""Authentification, droits d'accès aux données et journal des requêtes SQL."""
import hashlib, hmac, json, os, re, secrets, sqlite3, time
from contextlib import closing
from pathlib import Path

APP_DB = Path(os.environ.get("APP_DB_PATH", "app.db")).expanduser().resolve()
SESSION_TTL = 12 * 3600
_echecs: dict = {}
SQL_TIMEOUT = 5          # secondes max par requête générée par l'IA
SCHEMA_TTL = 60          # durée du cache du schéma (secondes)
_schema_cache: dict = {}
BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")


# --- Accès en lecture seule à la base métier (boutique.db) --------------------------
DATABASE_PATH = Path(os.environ.get("SQLITE_DB_PATH", "boutique.db")).expanduser().resolve()


def _connect_read_only() -> sqlite3.Connection:
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"Base SQLite introuvable : {DATABASE_PATH}. Lancez le serveur depuis le dossier contenant "
            "boutique.db ou définissez SQLITE_DB_PATH.")
    connection = sqlite3.connect(f"{DATABASE_PATH.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _remove_leading_comments(query: str) -> str:
    remaining = query.lstrip()
    while remaining.startswith("--") or remaining.startswith("/*"):
        if remaining.startswith("--"):
            end = remaining.find("\n")
            if end == -1:
                return ""
            remaining = remaining[end + 1:].lstrip()
            continue
        end = remaining.find("*/", 2)
        if end == -1:
            return ""
        remaining = remaining[end + 2:].lstrip()
    return remaining


def _validate_read_query(query: str) -> str:
    query = _remove_leading_comments(query.strip())
    if not query:
        raise ValueError("La requête SQL ne peut pas être vide.")
    if ";" in query.rstrip(";"):
        raise ValueError("Une seule requête SQL est autorisée.")
    if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", query, re.IGNORECASE):
        raise ValueError("Seules les requêtes SELECT, WITH et EXPLAIN sont autorisées.")
    return query.rstrip(";").strip()


def q(sql, args=(), one=False, write=False):
    """Exécute une requête sur la base applicative (comptes, conversations, logs)."""
    with closing(sqlite3.connect(APP_DB, timeout=10)) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA synchronous=NORMAL")   # avec WAL : commits bien plus rapides
        cur = c.execute(sql, args)
        if write:
            c.commit()
            return cur.lastrowid
        rows = [dict(r) for r in cur.fetchall()]
    return (rows[0] if rows else None) if one else rows


def init_db():
    with closing(sqlite3.connect(APP_DB, timeout=10)) as c:
        c.execute("PRAGMA journal_mode=WAL")     # lectures et écritures ne se bloquent plus
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
        CREATE TABLE IF NOT EXISTS gemini_log(id INTEGER PRIMARY KEY, user_id INTEGER, username TEXT,
            conv_id TEXT, kind TEXT, model TEXT, system_instruction TEXT, prompt TEXT, reponse TEXT,
            prompt_tokens INTEGER, response_tokens INTEGER, total_tokens INTEGER,
            duration_ms INTEGER, erreur TEXT, created_at REAL);
        """)
        # migration : e-mail des comptes + jetons de réinitialisation
        if "email" not in [r[1] for r in c.execute("PRAGMA table_info(users)")]:
            c.execute("ALTER TABLE users ADD COLUMN email TEXT")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users(email)")
        c.execute("CREATE TABLE IF NOT EXISTS resets(token_hash TEXT PRIMARY KEY, "
                  "user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires REAL NOT NULL)")
        # index : évite les parcours complets (listes, jointures, suppressions en cascade)
        c.executescript("""
        CREATE INDEX IF NOT EXISTS ix_messages_conv ON messages(conv_id, id);
        CREATE INDEX IF NOT EXISTS ix_conv_user ON conversations(user_id, created_at);
        CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS ix_resets_user ON resets(user_id);
        CREATE INDEX IF NOT EXISTS ix_log_date ON query_log(created_at);
        CREATE INDEX IF NOT EXISTS ix_gemini_log_date ON gemini_log(created_at);
        CREATE INDEX IF NOT EXISTS ix_gemini_log_user ON gemini_log(user_id);
        """)
        # migration (une seule fois) : anciens résultats avec des séquences \uXXXX -> texte lisible
        if c.execute("PRAGMA user_version").fetchone()[0] < 1:
            for mid, res in c.execute(r"SELECT id, resultats FROM messages WHERE resultats LIKE '%\u%'").fetchall():
                try:
                    c.execute("UPDATE messages SET resultats=? WHERE id=?",
                              (json.dumps(json.loads(res), ensure_ascii=False, default=str), mid))
                except ValueError:
                    pass
            c.execute("PRAGMA user_version=1")
        c.executemany("INSERT OR IGNORE INTO services(name) VALUES(?)",
                      [("Marketing",), ("Finance",), ("RH",), ("DSI",)])
        c.commit()
    if not q("SELECT 1 FROM users WHERE role='admin'", one=True):
        pwd = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
        creer_utilisateur(os.environ.get("ADMIN_USERNAME", "admin"), pwd, "admin")
        print(f"[SECURITE] Compte admin créé. Mot de passe initial : {pwd}  (à changer)")


# --- Mots de passe et sessions ------------------------------------------------

def hash_pw(p, salt=None):
    """Mots de passe stockés en clair (choix assumé) : aucune transformation."""
    return p


def check_pw(p, stored):
    """Comparaison en temps constant (évite de révéler le mot de passe par le temps de réponse)."""
    return hmac.compare_digest(str(p).encode(), str(stored).encode())


def creer_utilisateur(username, password, role="user", service_id=None, email=None):
    if len(password) < 10:
        raise ValueError("Le mot de passe doit contenir au moins 10 caractères.")
    return q("INSERT INTO users(username,pwd_hash,role,service_id,created_at,email) VALUES(?,?,?,?,?,?)",
             (username.strip(), hash_pw(password), role, service_id, time.time(), email), write=True)


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


# --- Récupération du mot de passe par e-mail --------------------------------------

def creer_reset(email):
    """Retourne (utilisateur, jeton) si l'e-mail correspond à un compte actif, sinon None.
    Jeton à usage unique, valable 30 min, stocké haché."""
    u = q("SELECT * FROM users WHERE lower(email)=lower(?) AND active=1", (email.strip(),), one=True)
    if not u:
        return None
    token = secrets.token_urlsafe(32)
    q("DELETE FROM resets WHERE user_id=?", (u["id"],), write=True)
    q("INSERT INTO resets VALUES(?,?,?)",
      (hashlib.sha256(token.encode()).hexdigest(), u["id"], time.time() + 1800), write=True)
    return u, token


def appliquer_reset(token, nouveau):
    if len(nouveau) < 10:
        raise ValueError("Le mot de passe doit contenir au moins 10 caractères.")
    h = hashlib.sha256(token.encode()).hexdigest()
    r = q("SELECT user_id FROM resets WHERE token_hash=? AND expires>?", (h, time.time()), one=True)
    if not r:
        raise ValueError("Lien invalide ou expiré. Refaites une demande de réinitialisation.")
    q("UPDATE users SET pwd_hash=? WHERE id=?", (hash_pw(nouveau), r["user_id"]), write=True)
    q("DELETE FROM resets WHERE user_id=?", (r["user_id"],), write=True)
    q("DELETE FROM sessions WHERE user_id=?", (r["user_id"],), write=True)


def envoyer_mail(dest, sujet, corps):
    """Envoi SMTP (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM).
    Sans SMTP_HOST (mode test), le message est affiché dans la console du serveur."""
    hote = os.environ.get("SMTP_HOST")
    if not hote:
        print(f"[SECURITE] SMTP non configuré. E-mail pour {dest} :\n{corps}")
        return
    import smtplib, ssl
    from email.message import EmailMessage
    m = EmailMessage()
    m["From"] = os.environ.get("SMTP_FROM") or os.environ.get("SMTP_USER", "")
    m["To"], m["Subject"] = dest, sujet
    m.set_content(corps)
    port = int(os.environ.get("SMTP_PORT", "587"))
    try:
        ctx = ssl.create_default_context()
        if port == 465:
            s = smtplib.SMTP_SSL(hote, port, timeout=15, context=ctx)
        else:
            s = smtplib.SMTP(hote, port, timeout=15)
            s.starttls(context=ctx)
        with s:
            if os.environ.get("SMTP_USER"):
                s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
            s.send_message(m)
    except Exception as e:
        print(f"[SECURITE] Échec d'envoi de l'e-mail : {e}")


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
    with closing(_connect_read_only()) as c:
        noms = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {t: [r[1] for r in c.execute(f'PRAGMA table_info("{t}")')] for t in noms}


def schema_text(allowed):
    """Schéma filtré selon les droits (mis en cache ~60 s). La clé contient les droits :
    si l'admin les modifie, un nouveau schéma est calculé automatiquement."""
    cle = None if allowed is None else tuple(sorted(
        (t, tuple(sorted(cols)) if cols is not None else None) for t, cols in allowed.items()))
    hit = _schema_cache.get(cle)
    if hit and time.time() - hit[0] < SCHEMA_TTL:
        return hit[1]
    texte = _schema_text_brut(allowed)
    _schema_cache[cle] = (time.time(), texte)
    return texte


def _schema_text_brut(allowed):
    """Schéma filtré selon les droits : c'est le seul que voit le modèle IA."""
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
    sql = _validate_read_query(sql)
    with closing(_connect_read_only()) as c:
        c.set_authorizer(_authorizer(allowed_for(user)))
        deadline = time.time() + SQL_TIMEOUT
        c.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000)  # coupe les requêtes trop longues
        try:
            cur = c.execute(sql)
            cols = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(max_rows + 1)
        except sqlite3.DatabaseError as e:
            if "not authorized" in str(e) or "prohibited" in str(e):
                raise PermissionError("Accès refusé : cette requête touche des données non autorisées pour votre service.") from e
            if "interrupted" in str(e):
                raise RuntimeError(f"Requête trop longue (limite {SQL_TIMEOUT} s) : ajoutez des filtres.") from e
            raise RuntimeError(f"Erreur SQLite : {e}") from e
    trunc = len(rows) > max_rows
    rows = rows[:max_rows]
    return {"columns": cols, "rows": [dict(zip(cols, r)) for r in rows],
            "row_count": len(rows), "truncated": trunc}


def log_query(user, question, sql, status, rows=0, ms=0):
    q("INSERT INTO query_log(user_id,username,question,sql,status,row_count,duration_ms,created_at) "
      "VALUES(?,?,?,?,?,?,?,?)", (user["id"], user["username"], question, sql, status, rows, ms, time.time()),
      write=True)


def log_gemini(user, conv_id, kind, model, system_instruction, prompt, reponse=None,
               prompt_tokens=None, response_tokens=None, total_tokens=None, duration_ms=0, erreur=None):
    """Journalise un échange avec Gemini (génération SQL ou formulation de réponse),
    visible dans Administration -> Échanges IA."""
    q("""INSERT INTO gemini_log(user_id,username,conv_id,kind,model,system_instruction,prompt,reponse,
                                 prompt_tokens,response_tokens,total_tokens,duration_ms,erreur,created_at)
         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (user["id"], user["username"], conv_id, kind, model, system_instruction, prompt, reponse,
       prompt_tokens, response_tokens, total_tokens, duration_ms, erreur, time.time()), write=True)