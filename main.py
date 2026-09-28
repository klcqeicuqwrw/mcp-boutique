"""Point d'entrée sécurisé : uvicorn main:app --port 8000
Réutilise la génération SQL / réponse Gemini de api.py."""
import csv, io, json, os, re, time, uuid
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import du module de sécurité personnalisé (gère la base de données utilisateurs, les logs, les permissions)
import securite as S
from google.genai import types
# Import des fonctions liées à l'IA créées dans api.py
from api import MessageHistorique, _appeler_gemini_avec_retry, formuler_reponse, generer_sql

# Regex pour détecter rapidement si la question de l'utilisateur implique de dessiner un graphique
MOTS_GRAPH = re.compile(r"graph|courbe|histogramme|camembert|diagramme|chart|plot", re.I)
# Types de graphiques supportés par le frontend (via Chart.js par exemple)
TYPES_GRAPH = ("bar", "line", "pie", "doughnut")

# ---------------------------------------------------------------------------
# Ce module est la couche "web + sécurité + orchestration".
# Il reçoit les requêtes HTTP, vérifie la session, choisit les bons droits,
# puis appelle le moteur SQL / Gemini et renvoie le résultat dans l'interface.
# ---------------------------------------------------------------------------

def choisir_graphique(question, res):
    """
    Choisit le type de graphique et les colonnes à utiliser.
    En cas d'échec de l'IA, utilise une méthode de secours (repli heuristique).
    """
    cols, rows = res["columns"], res["rows"]
    
    # Identifie quelles colonnes du résultat SQL contiennent uniquement des nombres
    est_num = lambda c: any(isinstance(r.get(c), (int, float)) for r in rows) and \
        all(r.get(c) is None or isinstance(r.get(c), (int, float)) for r in rows)
    nums = [c for c in cols if est_num(c)]
    
    # S'il n'y a pas assez de données pour faire un graphique, on annule
    if len(cols) < 2 or not rows or not nums:
        return None
        
    spec = None
    try:
        # On demande à Gemini d'analyser les données pour recommander le meilleur graphique
        r = _appeler_gemini_avec_retry(
            f"Question : {question}\nColonnes : {cols} (numériques : {nums})\n"
            f"Début des lignes : {json.dumps(rows[:3], ensure_ascii=False, default=str)}\n"
            f"Nombre de lignes : {len(rows)}\n"
            'Choisis le graphique le plus parlant. Réponds en JSON : {"type":"bar|line|pie|doughnut",'
            '"x":"colonne","y":["colonnes numériques"],"titre":"titre court"}. '
            "line = évolution dans le temps ; pie/doughnut = parts d'un tout (8 lignes max, un seul y) ; sinon bar.",
            types.GenerateContentConfig(temperature=0, response_mime_type="application/json"))
        spec = json.loads(r.text)
    except Exception:
        spec = None
        
    # Vérifie si le JSON renvoyé par l'IA est valide et correspond à nos colonnes
    ok = isinstance(spec, dict) and spec.get("type") in TYPES_GRAPH and spec.get("x") in cols \
        and isinstance(spec.get("y"), list) and spec["y"] and all(y in nums for y in spec["y"])
        
    # Si l'IA a échoué ou répondu n'importe quoi, on crée un graphique "Barres" par défaut
    if not ok:
        x = next((c for c in cols if c not in nums), cols[0]) # On prend la 1ère colonne texte pour l'axe X
        y = [c for c in nums if c != x][:1] # On prend la 1ère colonne numérique pour l'axe Y
        if not y:
            return None
        spec = {"type": "bar", "x": x, "y": y, "titre": question[:60]}
        
    # Les camemberts/doughnuts n'ont besoin que d'une seule série de données (un seul Y)
    if spec["type"] in ("pie", "doughnut"):
        spec["y"] = spec["y"][:1]
    spec["titre"] = str(spec.get("titre") or "")[:100] # Sécurité sur la longueur du titre
    return spec

# --- Configuration de l'application FastAPI ---

WEB = Path(__file__).parent / "web" # Dossier contenant les fichiers HTML/CSS/JS
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"  # Activer la sécurité des cookies en production (HTTPS)

app = FastAPI(title="Assistant baileur sociale")
S.init_db() # Initialise les tables de sécurité (utilisateurs, logs, permissions)
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static") # Sert les fichiers statiques (images, CSS)


# --- Dépendances (Filtres de sécurité) ------------------------------------------

def user_dep(request: Request):
    """
    Filtre : Vérifie si l'utilisateur est connecté en lisant son cookie 'session'.
    À injecter dans chaque route nécessitant une authentification.
    """
    u = S.user_from_token(request.cookies.get("session"))
    if not u:
        raise HTTPException(401, "Non authentifié")
    return u

def csrf(request: Request):
    """
    Filtre : Protection contre les attaques CSRF.
    N'autorise les modifications (POST, PATCH, DELETE) que si elles viennent de requêtes AJAX ('fetch').
    """
    if request.method not in ("GET", "HEAD") and request.headers.get("x-requested-with") != "fetch":
        raise HTTPException(403, "Requête refusée (CSRF)")

def admin_dep(u=Depends(user_dep)):
    """
    Filtre : Vérifie si l'utilisateur connecté possède le rôle 'admin'.
    """
    if u["role"] != "admin":
        raise HTTPException(403, "Réservé aux administrateurs")
    return u

# Applique la protection CSRF à toutes les routes de l'application
app.router.dependencies.append(Depends(csrf))


# --- Pages Web (Routes HTML) -----------------------------------------------------

def _user_or_none(request: Request):
    """Fonction utilitaire pour récupérer l'utilisateur sans déclencher d'erreur s'il n'est pas connecté."""
    return S.user_from_token(request.cookies.get("session"))

@app.get("/")
def accueil(request: Request):
    """Route principale (Racine). Redirige vers le Chat, l'Admin ou le Login selon l'état."""
    u = _user_or_none(request)
    if not u:
        # Non connecté -> Affiche la page de connexion sans la mettre en cache
        return FileResponse(WEB / "login.html", headers={"Cache-Control": "no-store"})
    # Connecté -> Redirection selon le rôle
    return RedirectResponse("/admin" if u["role"] == "admin" else "/chat")

@app.get("/reinit")
def page_reinit():
    """Page permettant de réinitialiser son mot de passe depuis un lien email."""
    return FileResponse(WEB / "reset.html")

@app.get("/chat")
def page_chat(request: Request):
    """Page contenant l'interface de conversation (Le Chatbot)."""
    if not _user_or_none(request):
        return RedirectResponse("/")
    return FileResponse(WEB / "index.html")

@app.get("/admin")
def page_admin(request: Request):
    """Page d'administration (gestion utilisateurs, logs, droits)."""
    u = _user_or_none(request)
    if not u:
        return RedirectResponse("/")
    if u["role"] != "admin":
        return RedirectResponse("/chat")
    return FileResponse(WEB / "admin.html")


# --- API : Authentification et Profil --------------------------------------------

class Login(BaseModel):
    username: str
    password: str

@app.post("/api/login")
def login(p: Login, response: Response):
    """Vérifie les identifiants et crée un cookie de session si valides."""
    try:
        token = S.login(p.username, p.password)
    except PermissionError as e:
        raise HTTPException(429, str(e)) # Trop de tentatives échouées
        
    if not token:
        raise HTTPException(401, "Identifiants invalides")
        
    # Place le jeton de sécurité dans un cookie HTTPOnly (invisible pour JavaScript)
    response.set_cookie("session", token, httponly=True, samesite="strict",
                        secure=COOKIE_SECURE, max_age=S.SESSION_TTL)
    u = S.user_from_token(token)
    if not u:
        raise HTTPException(500, "Session impossible à initialiser")
        
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True, "redirect": "/admin" if u["role"] == "admin" else "/chat"}

@app.post("/api/logout")
def logout(request: Request, response: Response):
    """Déconnecte l'utilisateur en invalidant son token côté serveur et côté navigateur."""
    if request.cookies.get("session"):
        S.logout(request.cookies["session"])
    response.delete_cookie("session")
    return {"ok": True}

@app.get("/api/me")
def me(u=Depends(user_dep)):
    """Renvoie les infos de l'utilisateur connecté (pour affichage dans l'UI)."""
    svc = S.q("SELECT name FROM services WHERE id=?", (u["service_id"],), one=True)
    return {"username": u["username"], "role": u["role"], "service": svc["name"] if svc else None}

class Oubli(BaseModel):
    email: str

class Reinit(BaseModel):
    token: str
    nouveau: str

_oublis: dict = {}

@app.post("/api/mdp-oublie")
def mdp_oublie(p: Oubli, bg: BackgroundTasks):
    """
    Génère un lien de réinitialisation de mot de passe.
    Sécurité : Limité à 3 envois par heure par e-mail pour éviter le spam.
    Renvoie toujours "ok" pour ne pas révéler si un compte existe ou non.
    """
    now, cle = time.time(), p.email.strip().lower()
    recents = [t for t in _oublis.get(cle, []) if now - t < 3600]
    if cle and len(recents) < 3:
        _oublis[cle] = recents + [now]
        r = S.creer_reset(cle)
        if r:
            u, token = r
            # Envoi de l'e-mail de manière asynchrone (en arrière-plan)
            bg.add_task(S.envoyer_mail, u["email"], "Réinitialisation de votre mot de passe",
                        f"Bonjour {u['username']},\n\nPour choisir un nouveau mot de passe (lien valable 30 minutes) :\n"
                        f"{S.BASE_URL}/reinit?token={token}\n\n"
                        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.")
    return {"ok": True}

@app.post("/api/reinit")
def reinit(p: Reinit):
    """Applique le nouveau mot de passe si le token (lien reçu par mail) est valide."""
    try:
        S.appliquer_reset(p.token, p.nouveau)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}

class Mdp(BaseModel):
    ancien: str
    nouveau: str

@app.post("/api/password")
def changer_mdp(p: Mdp, u=Depends(user_dep)):
    """Permet à un utilisateur connecté de modifier son mot de passe."""
    if not S.check_pw(p.ancien, u["pwd_hash"]):
        raise HTTPException(400, "Ancien mot de passe incorrect")
    if len(p.nouveau) < 10:
        raise HTTPException(400, "Au moins 10 caractères")
    S.q("UPDATE users SET pwd_hash=? WHERE id=?", (S.hash_pw(p.nouveau), u["id"]), write=True)
    return {"ok": True}


# --- API : Conversations (propres à chaque utilisateur) -------------------------

def _conv(conv_id, u):
    """Vérifie qu'une conversation existe ET qu'elle appartient bien à l'utilisateur connecté."""
    c = S.q("SELECT * FROM conversations WHERE id=? AND user_id=?", (conv_id, u["id"]), one=True)
    if not c:
        raise HTTPException(404, "Conversation introuvable")
    return c

@app.get("/api/conversations")
def lister_conv(u=Depends(user_dep)):
    """Renvoie la liste des conversations de l'utilisateur pour construire la barre latérale."""
    return S.q("""SELECT c.id, c.titre,
                         (SELECT group_concat(question, char(10)) FROM messages WHERE conv_id=c.id) AS questions
                  FROM conversations c WHERE c.user_id=? ORDER BY c.created_at DESC""", (u["id"],))

@app.get("/api/conversations/{cid}")
def lire_conv(cid: str, u=Depends(user_dep)):
    """Charge l'historique complet des messages pour une conversation donnée."""
    _conv(cid, u)
    msgs = S.q("SELECT id, question, reponse, sql AS sql_genere, resultats, erreur "
               "FROM messages WHERE conv_id=? ORDER BY id", (cid,))
    for m in msgs:
        m["resultats"] = json.loads(m["resultats"]) if m["resultats"] else None
    return {"messages": msgs}

class Titre(BaseModel):
    titre: str

@app.post("/api/conversations")
def creer_conv(u=Depends(user_dep)):
    """Crée une nouvelle conversation vide."""
    cid = str(uuid.uuid4())
    S.q("INSERT INTO conversations VALUES(?,?,?,?)", (cid, u["id"], None, time.time()), write=True)
    return {"id": cid, "titre": None, "messages": []}

@app.patch("/api/conversations/{cid}")
def renommer_conv(cid: str, p: Titre, u=Depends(user_dep)):
    """Change le nom affiché d'une conversation dans l'historique."""
    _conv(cid, u)
    S.q("UPDATE conversations SET titre=? WHERE id=?", (p.titre.strip()[:120], cid), write=True)
    return {"ok": True}

@app.delete("/api/conversations/{cid}")
def supprimer_conv(cid: str, u=Depends(user_dep)):
    """Supprime définitivement une conversation."""
    _conv(cid, u)
    S.q("DELETE FROM conversations WHERE id=?", (cid,), write=True)
    return {"ok": True}


# --- API : Question en langage naturel (Le Chatbot) ----------------------------

class Question(BaseModel):
    conv_id: str
    question: str
    veut_reponse: bool = True
    veut_tableau: bool = True

# Cache en mémoire : évite de redemander le même SQL à Gemini si la question est identique
_sql_cache: dict = {}
SQL_CACHE_TTL, SQL_CACHE_MAX = 600, 200 # Valide 10 min, max 200 requêtes en mémoire

@app.post("/api/ask")
def ask(p: Question, u=Depends(user_dep)):
    """
    Le cœur métier de l'application. Reçoit la question, filtre selon les droits,
    demande la requête SQL à Gemini, et l'exécute sur la base.
    """
    question = p.question.strip()
    if not question:
        raise HTTPException(400, "La question ne peut pas être vide.")
    conv = _conv(p.conv_id, u)
    
    # 1. Vérification des droits : on construit le schéma de la base UNIQUEMENT
    # avec les tables/colonnes que l'utilisateur a le droit de voir.
    allowed = S.allowed_for(u)
    try:
        schema = S.schema_text(allowed)
    except Exception as e:
        raise HTTPException(500, f"Base métier inaccessible : {e}")
    if not schema:
        raise HTTPException(403, "Aucune donnée n'est accessible à votre service. Contactez un administrateur.")

    # 2. Construction de l'historique récent pour le contexte IA
    hist = []
    for m in S.q("SELECT question, reponse FROM messages WHERE conv_id=? ORDER BY id DESC LIMIT 3", (conv["id"],))[::-1]:
        hist += [MessageHistorique(role="user", content=m["question"] or ""),
                 MessageHistorique(role="assistant", content=m["reponse"] or "(Tableau généré)")]

    def enregistrer(**kw):
        """Sous-fonction pour sauvegarder l'échange dans la base de données."""
        if conv["titre"] is None:
            # Nomme automatiquement la conversation avec la première question posée
            S.q("UPDATE conversations SET titre=? WHERE id=?", (question[:80], conv["id"]), write=True)
        return S.q("INSERT INTO messages(conv_id,question,reponse,sql,resultats,erreur,created_at) "
                   "VALUES(?,?,?,?,?,?,?)",
                   (conv["id"], question, kw.get("reponse"), kw.get("sql"),
                    json.dumps(kw["resultats"], default=str, ensure_ascii=False) if kw.get("resultats") else None,
                    kw.get("erreur"), time.time()), write=True)

    # 3. Génération du SQL par l'IA (ou utilisation du Cache)
    cle = (" ".join(question.lower().split()), hash(schema))
    en_cache = None if hist else _sql_cache.get(cle)
    if en_cache and time.time() - en_cache[0] < SQL_CACHE_TTL:
        sql = en_cache[1]
    else:
        journal = lambda **kw: S.log_gemini(u, conv["id"], **kw)
        try:
            sql = generer_sql(question, schema, hist, log=journal)
        except Exception as e:
            raise HTTPException(502, f"Erreur Gemini (génération SQL): {e}")

    # 4. Exécution de la requête SQL générée
    t0 = time.time()
    try:
        res = S.run_query(u, sql)
    except PermissionError as e:
        # L'IA a tenté d'interroger une table interdite pour cet utilisateur
        S.log_query(u, question, sql, "refusé")
        enregistrer(sql=sql, erreur=str(e))
        raise HTTPException(403, str(e))
    except (ValueError, RuntimeError) as e:
        # Requête SQL malformée ou erreur de base de données
        S.log_query(u, question, sql, "erreur")
        enregistrer(sql=sql, erreur=str(e))
        raise HTTPException(400, f"Requête invalide: {e}")
        
    S.log_query(u, question, sql, "ok", res["row_count"], int((time.time() - t0) * 1000))
    
    # Enregistrement dans le cache si la requête a réussi
    if not hist:
        if len(_sql_cache) >= SQL_CACHE_MAX:
            _sql_cache.clear()
        _sql_cache[cle] = (time.time(), sql)

    # 5. Préparation de la réponse
    rep, attente = "", False
    if p.veut_reponse:
        if res["row_count"] == 0:
            rep = "Aucun résultat."
        else:
            attente = True # Indique au client qu'il doit déclencher la route texte
            
    if not (p.veut_tableau or p.veut_reponse):
        p.veut_tableau = True # Sécurité : toujours afficher au moins le tableau
    if not p.veut_tableau:
        res["masque"] = True  # Le tableau est stocké (pour export PDF/CSV) mais caché à l'écran
        
    # 6. Vérification si un graphique est demandé
    if MOTS_GRAPH.search(question):
        g = choisir_graphique(question, res)
        if g:
            res["graphique"] = g
            
    # 7. Sauvegarde et renvoi des données
    mid = enregistrer(reponse=rep, sql=sql, resultats=res)
    return {"id": mid, "reponse": rep, "sql_genere": sql, "resultats": res, "texte_en_attente": attente}

@app.post("/api/ask/{mid}/texte")
def ask_texte(mid: int, u=Depends(user_dep)):
    """
    Seconde étape (asynchrone du point de vue de l'utilisateur) : 
    Demande à Gemini de formuler une réponse en Français à partir du tableau de résultats.
    """
    m = S.q("""SELECT m.question, m.reponse, m.resultats FROM messages m
               JOIN conversations c ON c.id=m.conv_id WHERE m.id=? AND c.user_id=?""", (mid, u["id"]), one=True)
    if not m or not m["resultats"]:
        raise HTTPException(404, "Message introuvable")
    if m["reponse"]:
        return {"reponse": m["reponse"]} # Déjà générée
        
    conv_id = S.q("SELECT conv_id FROM messages WHERE id=?", (mid,), one=True)["conv_id"]
    journal = lambda **kw: S.log_gemini(u, conv_id, **kw)
    try:
        rep = formuler_reponse(m["question"], json.loads(m["resultats"]), log=journal)
    except Exception as e:
        raise HTTPException(502, f"Erreur Gemini (formulation): {e}")
        
    S.q("UPDATE messages SET reponse=? WHERE id=?", (rep, mid), write=True)
    return {"reponse": rep}


# --- API : Export d'un tableau (CSV, PDF, Excel...) -----------------------------

def _cell(v):
    """
    Sécurité contre l'injection CSV (formules Excel exécutant des macros malveillantes).
    Ajoute une apostrophe devant les symboles sensibles.
    """
    v = "" if v is None else v
    return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r") else v

@app.get("/api/export/{mid}")
def exporter(mid: int, format: str = "csv", u=Depends(user_dep)):
    """Génère un fichier téléchargeable contenant les résultats SQL."""
    m = S.q("""SELECT m.resultats FROM messages m JOIN conversations c ON c.id=m.conv_id
               WHERE m.id=? AND c.user_id=?""", (mid, u["id"]), one=True)
    if not m or not m["resultats"]:
        raise HTTPException(404, "Aucun tableau à exporter")
        
    r = json.loads(m["resultats"])
    cols, rows = r["columns"], [[_cell(row.get(c)) for c in r["columns"]] for row in r["rows"]]
    nom = f"export_{mid}"
    
    # Logique de création des fichiers selon le format demandé (CSV, TSV, JSON, MD, PDF, XLSX)
    if format in ("csv", "tsv"):
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";" if format == "csv" else "\t")  # ";" pour être compatible Excel France
        w.writerow(cols); w.writerows(rows)
        # L'ajout du "\ufeff" (BOM) force Excel à lire le fichier en UTF-8 (sinon accents cassés)
        data, mime = ("\ufeff" + buf.getvalue()).encode("utf-8"), "text/csv; charset=utf-8"
    elif format == "json":
        data = json.dumps([dict(zip(cols, x)) for x in rows], ensure_ascii=False, indent=2, default=str).encode()
        mime = "application/json"
    elif format == "md": # Markdown (pour documentation technique)
        esc = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
        lignes = ["| " + " | ".join(map(esc, cols)) + " |", "|" + "---|" * len(cols)]
        lignes += ["| " + " | ".join(esc(v) for v in x) + " |" for x in rows]
        data, mime = "\n".join(lignes).encode(), "text/markdown; charset=utf-8"
    elif format == "pdf":
        try:
            # Reportlab est requis pour générer le PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        except ModuleNotFoundError:
            raise HTTPException(501, "Installez reportlab : pip install reportlab")
        from xml.sax.saxutils import escape
        styles = getSampleStyleSheet()
        st = styles["BodyText"]; st.fontSize, st.leading = 7, 9
        cell = lambda v: Paragraph(escape(str(v)), st)
        largeur = (landscape(A4)[0] - 48) / max(len(cols), 1)
        # Création et stylisation du tableau PDF
        t = Table([[cell(c) for c in cols]] + [[cell(v) for v in x] for x in rows],
                  colWidths=[largeur] * max(len(cols), 1), repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                               ("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        buf = io.BytesIO()
        SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=24, rightMargin=24,
                          topMargin=24, bottomMargin=24).build(
            [Paragraph("Export des résultats", styles["Heading3"]), Spacer(1, 6), t])
        data, mime = buf.getvalue(), "application/pdf"
    elif format == "xlsx":
        try:
            # Openpyxl est requis pour générer le fichier Excel
            from openpyxl import Workbook
        except ModuleNotFoundError:
            raise HTTPException(501, "Installez openpyxl : pip install openpyxl")
        wb = Workbook(); ws = wb.active
        ws.append(cols)
        for x in rows:
            ws.append([v if isinstance(v, (int, float, str)) else str(v) for v in x])
        buf = io.BytesIO(); wb.save(buf)
        data, mime = buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise HTTPException(400, "Format inconnu (csv, tsv, json, md, xlsx, pdf)")
        
    ext = "md" if format == "md" else format
    return Response(data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{nom}.{ext}"'})


# --- API : Administration (Droits "admin_dep" obligatoires) --------------------

class NouvelUtilisateur(BaseModel):
    username: str
    password: str
    role: str = "user"
    service_id: Optional[int] = None
    email: Optional[str] = None

class ModifUtilisateur(BaseModel):
    role: Optional[str] = None
    service_id: Optional[int] = None
    active: Optional[bool] = None
    password: Optional[str] = None
    email: Optional[str] = None

@app.get("/api/admin/users")
def admin_users(_=Depends(admin_dep)):
    """Liste tous les utilisateurs, leur statut et leur service (département)."""
    return S.q("""SELECT u.id, u.username, u.email, u.role, u.active, u.service_id, s.name AS service, u.created_at
                  FROM users u LEFT JOIN services s ON s.id=u.service_id ORDER BY u.username""")

@app.post("/api/admin/users")
def admin_creer_user(p: NouvelUtilisateur, _=Depends(admin_dep)):
    """Crée un nouvel utilisateur."""
    if p.role not in ("admin", "user"):
        raise HTTPException(400, "Rôle invalide")
    try:
        return {"id": S.creer_utilisateur(p.username, p.password, p.role, p.service_id, (p.email or "").strip() or None)}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(400, "Nom d'utilisateur ou e-mail déjà utilisé, ou service invalide")

@app.patch("/api/admin/users/{uid}")
def admin_modifier_user(uid: int, p: ModifUtilisateur, a=Depends(admin_dep)):
    """Met à jour un utilisateur (Désactivation, chgt de service, mdp)."""
    # Protection : un admin ne peut pas se retirer ses propres droits admin ou se désactiver
    if uid == a["id"] and (p.active is False or (p.role and p.role != "admin")):
        raise HTTPException(400, "Vous ne pouvez pas retirer vos propres droits d'admin")
        
    d = p.model_dump(exclude_unset=True)
    if "role" in d and d["role"] not in ("admin", "user"):
        raise HTTPException(400, "Rôle invalide")
        
    # Mise à jour du mot de passe
    if "password" in d:
        if len(d["password"]) < 10:
            raise HTTPException(400, "Au moins 10 caractères")
        S.q("UPDATE users SET pwd_hash=? WHERE id=?", (S.hash_pw(d.pop("password")), uid), write=True)
        # Invalide les sessions existantes de cet utilisateur
        S.q("DELETE FROM sessions WHERE user_id=?", (uid,), write=True)
        
    # Mise à jour de l'email
    if "email" in d:
        try:
            S.q("UPDATE users SET email=? WHERE id=?", ((d["email"] or "").strip() or None, uid), write=True)
        except Exception:
            raise HTTPException(400, "Adresse e-mail déjà utilisée")
            
    # Mise à jour des autres paramètres
    for champ in ("role", "service_id", "active"):
        if champ in d:
            S.q(f"UPDATE users SET {champ}=? WHERE id=?", (int(d[champ]) if champ == "active" else d[champ], uid), write=True)
            
    # Si le compte est désactivé, on le déconnecte immédiatement
    if d.get("active") is False:
        S.q("DELETE FROM sessions WHERE user_id=?", (uid,), write=True)
    return {"ok": True}

class NomService(BaseModel):
    name: str

@app.get("/api/admin/services")
def admin_services(_=Depends(admin_dep)):
    """Renvoie la liste des services avec leurs permissions respectives par table."""
    svcs = S.q("SELECT id, name FROM services ORDER BY name")
    for s in svcs:
        s["permissions"] = [{"table": r["table_name"], "columns": json.loads(r["columns"]) if r["columns"] else None}
                            for r in S.q("SELECT table_name, columns FROM permissions WHERE service_id=?", (s["id"],))]
    return svcs

@app.post("/api/admin/services")
def admin_creer_service(p: NomService, _=Depends(admin_dep)):
    """Ajoute un nouveau service (ex: RH, Marketing, Comptabilité)."""
    try:
        return {"id": S.q("INSERT INTO services(name) VALUES(?)", (p.name.strip(),), write=True)}
    except Exception:
        raise HTTPException(400, "Nom de service déjà utilisé")

class Droit(BaseModel):
    table: str
    columns: Optional[List[str]] = None  # Si None, l'utilisateur a accès à toutes les colonnes de la table

@app.put("/api/admin/services/{sid}/permissions")
def admin_droits(sid: int, droits: List[Droit], _=Depends(admin_dep)):
    """Remplace l'ensemble des droits d'accès aux tables pour un service donné."""
    connues = S.tables_info() # Récupère le schéma réel de la BDD
    
    # Nettoie les anciens droits
    S.q("DELETE FROM permissions WHERE service_id=?", (sid,), write=True)
    
    # Insère les nouveaux droits en s'assurant que les tables demandées existent bien
    for d in droits:
        if d.table not in connues or (d.columns and not set(d.columns) <= set(connues[d.table])):
            raise HTTPException(400, f"Table ou colonne inconnue : {d.table}")
        S.q("INSERT INTO permissions VALUES(?,?,?)",
            (sid, d.table, json.dumps(d.columns) if d.columns else None), write=True)
    return {"ok": True}

@app.get("/api/admin/schema")
def admin_schema(_=Depends(admin_dep)):
    """Affiche le schéma complet de la base de données (pour configurer les droits)."""
    try:
        return S.tables_info()
    except Exception as e:
        raise HTTPException(500, f"Base métier inaccessible : {e}")

@app.get("/api/admin/logs")
def admin_logs(username: str = "", status: str = "", limit: int = 200, _=Depends(admin_dep)):
    """Journal de toutes les requêtes SQL effectuées sur l'application."""
    return S.q("""SELECT id, username, question, sql, status, row_count, duration_ms, created_at
                  FROM query_log WHERE (?='' OR username=?) AND (?='' OR status=?)
                  ORDER BY id DESC LIMIT ?""", (username, username, status, status, min(limit, 1000)))

@app.get("/api/admin/gemini-logs")
def admin_gemini_logs(username: str = "", kind: str = "", limit: int = 200, _=Depends(admin_dep)):
    """Journal technique des échanges avec l'IA Gemini (pour traquer les coûts et les erreurs de prompt)."""
    return S.q("""SELECT id, username, conv_id, kind, model, system_instruction, prompt, reponse,
                         prompt_tokens, response_tokens, total_tokens, duration_ms, erreur, created_at
                  FROM gemini_log WHERE (?='' OR username=?) AND (?='' OR kind=?)
                  ORDER BY id DESC LIMIT ?""", (username, username, kind, kind, min(limit, 1000)))

@app.get("/api/admin/gemini-logs/stats")
def admin_gemini_stats(_=Depends(admin_dep)):
    """Retourne les statistiques de consommation (Tokens) de l'API Google Gemini."""
    jour, semaine = time.time() - 86400, time.time() - 7 * 86400
    def total(depuis):
        r = S.q("SELECT COUNT(*) n, COALESCE(SUM(total_tokens),0) t FROM gemini_log WHERE created_at>=?",
                (depuis,), one=True)
        return {"echanges": r["n"], "tokens": r["t"]}
    return {"jour": total(jour), "semaine": total(semaine), "total": total(0)}