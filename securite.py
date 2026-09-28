"""
Authentification, droits d'accès aux données et journal des requêtes SQL[cite: 4].
Ce module gère toute la sécurité de l'application : connexion, sessions, 
réinitialisation de mot de passe, et surtout le filtrage des droits d'accès 
aux données métier pour l'IA[cite: 4].
"""
import hashlib, hmac, json, os, re, secrets, sqlite3, time
from contextlib import closing
from pathlib import Path

# --- Configuration globale ---
# Base de données applicative (stocke les utilisateurs, les logs, les discussions)[cite: 4]
APP_DB = Path(os.environ.get("APP_DB_PATH", "app.db")).expanduser().resolve()
# Durée de vie d'une session utilisateur (12 heures)[cite: 4]
SESSION_TTL = 12 * 3600
# Dictionnaire pour tracker les échecs de connexion (protection anti brute-force)[cite: 4]
_echecs: dict = {}
# Temps maximum autorisé pour l'exécution d'une requête SQL générée par l'IA[cite: 4]
SQL_TIMEOUT = 5          
# Durée de validité du cache du schéma de la base de données (60 secondes)[cite: 4]
SCHEMA_TTL = 60          
_schema_cache: dict = {}
# URL de base pour les liens envoyés par e-mail (ex: réinitialisation mdp)[cite: 4]
BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")


# --- Accès en lecture seule à la base métier (bailleur_social.db) --------------------------
# Base de données métier (stocke les données réelles de l'entreprise)[cite: 4]
DATABASE_PATH = Path(os.environ.get("SQLITE_DB_PATH", "bailleur_social.db")).expanduser().resolve()


def _connect_read_only() -> sqlite3.Connection:
    """Ouvre une connexion à la base métier STRICTEMENT en mode lecture seule[cite: 4]."""
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"Base SQLite introuvable : {DATABASE_PATH}. Lancez le serveur depuis le dossier contenant "
            "bailleur_social.db ou définissez SQLITE_DB_PATH.")
    # Le paramètre ?mode=ro empêche physiquement toute modification des données[cite: 4]
    connection = sqlite3.connect(f"{DATABASE_PATH.as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _remove_leading_comments(query: str) -> str:
    """Nettoie les commentaires en début de requête SQL pour éviter de tromper la validation[cite: 4]."""
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
    """Vérifie que la requête ne contient que des instructions de lecture inoffensives[cite: 4]."""
    query = _remove_leading_comments(query.strip())
    if not query:
        raise ValueError("La requête SQL ne peut pas être vide.")
    # Interdit l'enchaînement de plusieurs requêtes (ex: SELECT * FROM X; DELETE FROM Y)[cite: 4]
    if ";" in query.rstrip(";"):
        raise ValueError("Une seule requête SQL est autorisée.")
    # Bloque toutes les commandes de type INSERT, UPDATE, DELETE, DROP, etc[cite: 4].
    if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", query, re.IGNORECASE):
        raise ValueError("Seules les requêtes SELECT, WITH et EXPLAIN sont autorisées.")
    return query.rstrip(";").strip()


# --- Gestion de la base applicative (app.db) -----------------------------------------------

def q(sql, args=(), one=False, write=False):
    """
    Exécute une requête sur la base APPLICATIVE (comptes, conversations, logs)[cite: 4].
    `one=True` : retourne un seul enregistrement sous forme de dictionnaire[cite: 4].
    `write=True` : exécute une modification (INSERT/UPDATE/DELETE) et sauvegarde (commit)[cite: 4].
    """
    with closing(sqlite3.connect(APP_DB, timeout=10)) as c:
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON") # Active la contrainte d'intégrité des clés étrangères[cite: 4]
        c.execute("PRAGMA synchronous=NORMAL")   # Optimisation des performances d'écriture avec WAL[cite: 4]
        cur = c.execute(sql, args)
        if write:
            c.commit()
            return cur.lastrowid
        rows = [dict(r) for r in cur.fetchall()]
    return (rows[0] if rows else None) if one else rows


def init_db():
    """Initialise la base de données applicative au démarrage du serveur[cite: 4]."""
    with closing(sqlite3.connect(APP_DB, timeout=10)) as c:
        # Le mode WAL (Write-Ahead Logging) permet de lire et écrire en même temps sans se bloquer[cite: 4]
        c.execute("PRAGMA journal_mode=WAL")     
        # Création de toutes les tables nécessaires au fonctionnement de l'app (utilisateurs, logs, discussions)[cite: 4]
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
        # Migration automatique : ajout du champ e-mail si la table existe depuis une ancienne version[cite: 4]
        if "email" not in [r[1] for r in c.execute("PRAGMA table_info(users)")]:
            c.execute("ALTER TABLE users ADD COLUMN email TEXT")
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users(email)")
        c.execute("CREATE TABLE IF NOT EXISTS resets(token_hash TEXT PRIMARY KEY, "
                  "user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires REAL NOT NULL)")
        
        # Création des index pour accélérer les recherches fréquentes dans la BDD[cite: 4]
        c.executescript("""
        CREATE INDEX IF NOT EXISTS ix_messages_conv ON messages(conv_id, id);
        CREATE INDEX IF NOT EXISTS ix_conv_user ON conversations(user_id, created_at);
        CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS ix_resets_user ON resets(user_id);
        CREATE INDEX IF NOT EXISTS ix_log_date ON query_log(created_at);
        CREATE INDEX IF NOT EXISTS ix_gemini_log_date ON gemini_log(created_at);
        CREATE INDEX IF NOT EXISTS ix_gemini_log_user ON gemini_log(user_id);
        """)
        
        # Migration des données JSON encodées en Unicode vers du texte lisible[cite: 4]
        if c.execute("PRAGMA user_version").fetchone()[0] < 1:
            for mid, res in c.execute(r"SELECT id, resultats FROM messages WHERE resultats LIKE '%\u%'").fetchall():
                try:
                    c.execute("UPDATE messages SET resultats=? WHERE id=?",
                              (json.dumps(json.loads(res), ensure_ascii=False, default=str), mid))
                except ValueError:
                    pass
            c.execute("PRAGMA user_version=1")
            
        # Création de services par défaut s'ils n'existent pas[cite: 4]
        c.executemany("INSERT OR IGNORE INTO services(name) VALUES(?)",
                      [("Marketing",), ("Finance",), ("RH",), ("DSI",)])
        c.commit()
        
    # Crée un compte administrateur automatiquement au premier lancement s'il n'y en a aucun[cite: 4]
    if not q("SELECT 1 FROM users WHERE role='admin'", one=True):
        pwd = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)
        creer_utilisateur(os.environ.get("ADMIN_USERNAME", "admin"), pwd, "admin")
        print(f"[SECURITE] Compte admin créé. Mot de passe initial : {pwd}  (à changer)")


# --- Mots de passe et sessions ------------------------------------------------

def hash_pw(p, salt=None):
    """Mots de passe stockés en clair (choix assumé pour ce projet spécifique) : aucune transformation[cite: 4]."""
    return p


def check_pw(p, stored):
    """Comparaison de mots de passe en temps constant (évite les attaques temporelles qui révèlent des infos)[cite: 4]."""
    return hmac.compare_digest(str(p).encode(), str(stored).encode())


def creer_utilisateur(username, password, role="user", service_id=None, email=None):
    """Crée un nouvel utilisateur en forçant une longueur minimale de mot de passe[cite: 4]."""
    if len(password) < 10:
        raise ValueError("Le mot de passe doit contenir au moins 10 caractères.")
    return q("INSERT INTO users(username,pwd_hash,role,service_id,created_at,email) VALUES(?,?,?,?,?,?)",
             (username.strip(), hash_pw(password), role, service_id, time.time(), email), write=True)


def login(username, password):
    """
    Système de connexion sécurisé. Retourne un jeton (token) de session ou None.
    Intègre une limite stricte à 5 échecs par période de 5 minutes par compte (anti brute-force)[cite: 4].
    """
    now = time.time()
    # Récupère l'historique récent des échecs pour cet utilisateur[cite: 4]
    tentatives = [t for t in _echecs.get(username, []) if now - t < 300]
    if len(tentatives) >= 5:
        raise PermissionError("Trop de tentatives. Réessayez dans quelques minutes.")
        
    u = q("SELECT * FROM users WHERE username=? AND active=1", (username,), one=True)
    # Vérification factice (hash_pw("x")) si le compte n'existe pas pour toujours prendre
    # le même temps de calcul (évite de dévoiler si un identifiant existe ou non)[cite: 4]
    ok = check_pw(password, u["pwd_hash"] if u else hash_pw("x"))
    
    if not (u and ok):
        _echecs[username] = tentatives + [now] # Ajoute cet échec à l'historique[cite: 4]
        return None
        
    _echecs.pop(username, None) # Remise à zéro des échecs en cas de succès[cite: 4]
    
    # Génération d'un token aléatoire sécurisé pour la session[cite: 4]
    token = secrets.token_urlsafe(32)
    # Le token est haché en BDD (si la BDD est volée, les sessions ne peuvent pas être usurpées)[cite: 4]
    q("INSERT INTO sessions VALUES(?,?,?)",
      (hashlib.sha256(token.encode()).hexdigest(), u["id"], now + SESSION_TTL), write=True)
    return token


def user_from_token(token):
    """Récupère les informations de l'utilisateur à partir de son jeton de session (s'il est valide)[cite: 4]."""
    if not token:
        return None
    return q("""SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id
                WHERE s.token_hash=? AND s.expires>? AND u.active=1""",
             (hashlib.sha256(token.encode()).hexdigest(), time.time()), one=True)


def logout(token):
    """Détruit la session en base de données[cite: 4]."""
    q("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),), write=True)


# --- Récupération du mot de passe par e-mail --------------------------------------

def creer_reset(email):
    """
    Génère un jeton de réinitialisation de mot de passe à usage unique (valable 30 min).
    Retourne (utilisateur, jeton) si l'e-mail correspond à un compte actif, sinon None[cite: 4].
    """
    u = q("SELECT * FROM users WHERE lower(email)=lower(?) AND active=1", (email.strip(),), one=True)
    if not u:
        return None
    token = secrets.token_urlsafe(32)
    q("DELETE FROM resets WHERE user_id=?", (u["id"],), write=True) # Supprime les anciens jetons[cite: 4]
    q("INSERT INTO resets VALUES(?,?,?)",
      (hashlib.sha256(token.encode()).hexdigest(), u["id"], time.time() + 1800), write=True)
    return u, token


def appliquer_reset(token, nouveau):
    """Valide le jeton et applique le nouveau mot de passe[cite: 4]."""
    if len(nouveau) < 10:
        raise ValueError("Le mot de passe doit contenir au moins 10 caractères.")
    h = hashlib.sha256(token.encode()).hexdigest()
    r = q("SELECT user_id FROM resets WHERE token_hash=? AND expires>?", (h, time.time()), one=True)
    if not r:
        raise ValueError("Lien invalide ou expiré. Refaites une demande de réinitialisation.")
        
    q("UPDATE users SET pwd_hash=? WHERE id=?", (hash_pw(nouveau), r["user_id"]), write=True)
    # Nettoie le jeton de reset et déconnecte l'utilisateur de toutes ses sessions actives[cite: 4]
    q("DELETE FROM resets WHERE user_id=?", (r["user_id"],), write=True)
    q("DELETE FROM sessions WHERE user_id=?", (r["user_id"],), write=True)


def envoyer_mail(dest, sujet, corps):
    """
    Fonction d'envoi d'e-mail via SMTP. 
    Si la configuration SMTP_HOST manque (ex: développement), le message s'affiche juste dans la console[cite: 4].
    """
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


# --- Droits d'accès aux données (Sécurité Granulaire) --------------------------

def allowed_for(user):
    """
    Transforme les droits configurés pour le service de l'utilisateur en un dictionnaire python simple.
    Exemple de retour : {'clients': {'id', 'nom'}, 'produits': None} (None = toutes les colonnes)
    Si l'utilisateur est admin, retourne None (accès illimité)[cite: 4].
    """
    if user["role"] == "admin":
        return None
    if not user["service_id"]:
        return {} # Aucun service = aucun accès[cite: 4]
        
    rows = q("SELECT table_name, columns FROM permissions WHERE service_id=?", (user["service_id"],))
    return {r["table_name"].lower(): ({c.lower() for c in json.loads(r["columns"])} if r["columns"] else None)
            for r in rows}


def _authorizer(allowed):
    """
    Génère un Callback (fonction de contrôle) pour le moteur SQLite.
    Ce mécanisme intercepte ABSOLUMENT TOUTES les tentatives de lecture dans la base de données
    au moment de l'exécution, et les bloque si l'utilisateur n'a pas les droits[cite: 4].
    Même si l'IA génère une sous-requête complexe ou utilise une vue, cette sécurité l'arrêtera[cite: 4].
    """
    def check(action, a1, a2, _db, _src):
        if action == sqlite3.SQLITE_READ:
            # Interdit de lire les tables internes de SQLite[cite: 4]
            if a1.lower().startswith("sqlite_"):
                return sqlite3.SQLITE_DENY
            # Si allowed est None (admin), on autorise[cite: 4]
            if allowed is None:
                return sqlite3.SQLITE_OK
            # Si la table ciblée (a1) n'est pas dans la liste des tables autorisées, on bloque[cite: 4]
            if a1.lower() not in allowed:
                return sqlite3.SQLITE_DENY
                
            cols = allowed[a1.lower()]
            # Si des colonnes spécifiques sont définies, on vérifie que la colonne cible (a2) est autorisée[cite: 4]
            return sqlite3.SQLITE_OK if (cols is None or not a2 or a2.lower() in cols) else sqlite3.SQLITE_DENY
            
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION, sqlite3.SQLITE_RECURSIVE):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    return check


def tables_info():
    """Récupère l'intégralité du schéma de la base métier sous forme de dictionnaire {table: [colonnes]}[cite: 4]."""
    with closing(_connect_read_only()) as c:
        noms = [r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {t: [r[1] for r in c.execute(f'PRAGMA table_info("{t}")')] for t in noms}


def schema_text(allowed):
    """
    Crée le texte représentant le schéma de la BDD à envoyer dans le prompt Gemini.
    Ce schéma est amputé des tables et colonnes que l'utilisateur n'a pas le droit de voir[cite: 4].
    Ce texte est mis en cache pour gagner en performance[cite: 4].
    """
    cle = None if allowed is None else tuple(sorted(
        (t, tuple(sorted(cols)) if cols is not None else None) for t, cols in allowed.items()))
    hit = _schema_cache.get(cle)
    
    # Utilise le cache s'il est encore valide[cite: 4]
    if hit and time.time() - hit[0] < SCHEMA_TTL:
        return hit[1]
        
    texte = _schema_text_brut(allowed)
    _schema_cache[cle] = (time.time(), texte)
    return texte


def _schema_text_brut(allowed):
    """Logique d'extraction et de formatage du schéma filtré (tables, colonnes, clés étrangères)[cite: 4]."""
    lignes = []
    with closing(_connect_read_only()) as c:
        for t in tables_info():
            # Filtre les tables interdites[cite: 4]
            if allowed is not None and t.lower() not in allowed:
                continue
                
            cols = allowed[t.lower()] if allowed is not None else None
            # Filtre les colonnes interdites[cite: 4]
            info = [f"{r[1]} {r[2]}" for r in c.execute(f'PRAGMA table_info("{t}")')
                    if cols is None or r[1].lower() in cols]
            ligne = f"{t}({', '.join(info)})"
            
            # Récupère et filtre les relations (clés étrangères)[cite: 4]
            fks = [f"{r[3]}->{r[2]}.{r[4]}" for r in c.execute(f'PRAGMA foreign_key_list("{t}")')
                   if allowed is None or r[2].lower() in allowed]
            lignes.append(ligne + (" FK: " + ", ".join(fks) if fks else ""))
    return "\n".join(lignes)


def run_query(user, sql, max_rows=500):
    """
    Exécute la requête SQL générée par l'IA sur la base métier.
    C'est ici que les filtres de sécurité sont concrètement appliqués au moment de l'exécution[cite: 4].
    """
    sql = _validate_read_query(sql) # Vérifie d'abord que c'est un SELECT[cite: 4]
    
    with closing(_connect_read_only()) as c:
        # Applique la politique de sécurité de l'utilisateur à la connexion SQLite[cite: 4]
        c.set_authorizer(_authorizer(allowed_for(user)))
        
        # Définit un délai d'exécution max (timeout) pour éviter qu'une requête IA mal optimisée ne bloque le serveur[cite: 4]
        deadline = time.time() + SQL_TIMEOUT
        c.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 100000) 
        
        try:
            cur = c.execute(sql)
            cols = [d[0] for d in cur.description or []]
            rows = cur.fetchmany(max_rows + 1)
        except sqlite3.DatabaseError as e:
            # Gestion des erreurs personnalisées si la requête touche des données interdites ou prend trop de temps[cite: 4]
            if "not authorized" in str(e) or "prohibited" in str(e):
                raise PermissionError("Accès refusé : cette requête touche des données non autorisées pour votre service.") from e
            if "interrupted" in str(e):
                raise RuntimeError(f"Requête trop longue (limite {SQL_TIMEOUT} s) : ajoutez des filtres.") from e
            raise RuntimeError(f"Erreur SQLite : {e}") from e
            
    # Tronque les résultats si on dépasse la limite[cite: 4]
    trunc = len(rows) > max_rows
    rows = rows[:max_rows]
    return {"columns": cols, "rows": [dict(zip(cols, r)) for r in rows],
            "row_count": len(rows), "truncated": trunc}


# --- Journalisation (Logging) --------------------------------------------------

def log_query(user, question, sql, status, rows=0, ms=0):
    """Enregistre en base applicative les questions posées et les requêtes SQL exécutées[cite: 4]."""
    q("INSERT INTO query_log(user_id,username,question,sql,status,row_count,duration_ms,created_at) "
      "VALUES(?,?,?,?,?,?,?,?)", (user["id"], user["username"], question, sql, status, rows, ms, time.time()),
      write=True)


def log_gemini(user, conv_id, kind, model, system_instruction, prompt, reponse=None,
               prompt_tokens=None, response_tokens=None, total_tokens=None, duration_ms=0, erreur=None):
    """
    Journalise en base applicative chaque échange avec l'API Google Gemini.
    Utile pour la facturation (tokens), le débogage (erreur) et l'audit (prompts envoyés)[cite: 4].
    """
    q("""INSERT INTO gemini_log(user_id,username,conv_id,kind,model,system_instruction,prompt,reponse,
                                 prompt_tokens,response_tokens,total_tokens,duration_ms,erreur,created_at)
         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (user["id"], user["username"], conv_id, kind, model, system_instruction, prompt, reponse,
       prompt_tokens, response_tokens, total_tokens, duration_ms, erreur, time.time()), write=True)