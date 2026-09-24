"""Point d'entrée sécurisé : uvicorn main:app --port 8000
Réutilise la génération SQL / réponse Gemini de api.py."""
import csv, io, json, os, re, time, uuid
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import securite as S
from google.genai import types
from api import MessageHistorique, _appeler_gemini_avec_retry, formuler_reponse, generer_sql

MOTS_GRAPH = re.compile(r"graph|courbe|histogramme|camembert|diagramme|chart|plot", re.I)
TYPES_GRAPH = ("bar", "line", "pie", "doughnut")


def choisir_graphique(question, res):
    """Choisit type de graphique et colonnes ; repli heuristique si l'IA échoue."""
    cols, rows = res["columns"], res["rows"]
    est_num = lambda c: any(isinstance(r.get(c), (int, float)) for r in rows) and \
        all(r.get(c) is None or isinstance(r.get(c), (int, float)) for r in rows)
    nums = [c for c in cols if est_num(c)]
    if len(cols) < 2 or not rows or not nums:
        return None
    spec = None
    try:
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
    ok = isinstance(spec, dict) and spec.get("type") in TYPES_GRAPH and spec.get("x") in cols \
        and isinstance(spec.get("y"), list) and spec["y"] and all(y in nums for y in spec["y"])
    if not ok:
        x = next((c for c in cols if c not in nums), cols[0])
        y = [c for c in nums if c != x][:1]
        if not y:
            return None
        spec = {"type": "bar", "x": x, "y": y, "titre": question[:60]}
    if spec["type"] in ("pie", "doughnut"):
        spec["y"] = spec["y"][:1]
    spec["titre"] = str(spec.get("titre") or "")[:100]
    return spec

WEB = Path(__file__).parent / "web"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"  # mettre 1 derrière HTTPS
app = FastAPI(title="Assistant Boutique (sécurisé)")
S.init_db()
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


# --- Dépendances ----------------------------------------------------------------

def user_dep(request: Request):
    u = S.user_from_token(request.cookies.get("session"))
    if not u:
        raise HTTPException(401, "Non authentifié")
    return u


def csrf(request: Request):
    if request.method not in ("GET", "HEAD") and request.headers.get("x-requested-with") != "fetch":
        raise HTTPException(403, "Requête refusée (CSRF)")


def admin_dep(u=Depends(user_dep)):
    if u["role"] != "admin":
        raise HTTPException(403, "Réservé aux administrateurs")
    return u


app.router.dependencies.append(Depends(csrf))


# --- Pages ------------------------------------------------------------------------

def _user_or_none(request: Request):
    return S.user_from_token(request.cookies.get("session"))


@app.get("/")
def accueil(request: Request):
    """Non connecté -> connexion ; admin -> /admin ; utilisateur -> /chat."""
    u = _user_or_none(request)
    if not u:
        return FileResponse(WEB / "login.html", headers={"Cache-Control": "no-store"})
    return RedirectResponse("/admin" if u["role"] == "admin" else "/chat")


@app.get("/reinit")
def page_reinit():
    return FileResponse(WEB / "reset.html")


@app.get("/chat")
def page_chat(request: Request):
    if not _user_or_none(request):
        return RedirectResponse("/")
    return FileResponse(WEB / "index.html")


@app.get("/admin")
def page_admin(request: Request):
    u = _user_or_none(request)
    if not u:
        return RedirectResponse("/")
    if u["role"] != "admin":
        return RedirectResponse("/chat")
    return FileResponse(WEB / "admin.html")


# --- Authentification -------------------------------------------------------------

class Login(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(p: Login, response: Response):
    try:
        token = S.login(p.username, p.password)
    except PermissionError as e:
        raise HTTPException(429, str(e))
    if not token:
        raise HTTPException(401, "Identifiants invalides")
    response.set_cookie("session", token, httponly=True, samesite="strict",
                        secure=COOKIE_SECURE, max_age=S.SESSION_TTL)
    u = S.user_from_token(token)
    if not u:
        raise HTTPException(500, "Session impossible à initialiser")
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True, "redirect": "/admin" if u["role"] == "admin" else "/chat"}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    if request.cookies.get("session"):
        S.logout(request.cookies["session"])
    response.delete_cookie("session")
    return {"ok": True}


@app.get("/api/me")
def me(u=Depends(user_dep)):
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
    """Réponse identique que l'e-mail existe ou non (pas d'énumération de comptes).
    Limite : 3 demandes par heure et par adresse."""
    now, cle = time.time(), p.email.strip().lower()
    recents = [t for t in _oublis.get(cle, []) if now - t < 3600]
    if cle and len(recents) < 3:
        _oublis[cle] = recents + [now]
        r = S.creer_reset(cle)
        if r:
            u, token = r
            bg.add_task(S.envoyer_mail, u["email"], "Réinitialisation de votre mot de passe",
                        f"Bonjour {u['username']},\n\nPour choisir un nouveau mot de passe (lien valable 30 minutes) :\n"
                        f"{S.BASE_URL}/reinit?token={token}\n\n"
                        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.")
    return {"ok": True}


@app.post("/api/reinit")
def reinit(p: Reinit):
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
    if not S.check_pw(p.ancien, u["pwd_hash"]):
        raise HTTPException(400, "Ancien mot de passe incorrect")
    if len(p.nouveau) < 10:
        raise HTTPException(400, "Au moins 10 caractères")
    S.q("UPDATE users SET pwd_hash=? WHERE id=?", (S.hash_pw(p.nouveau), u["id"]), write=True)
    return {"ok": True}


# --- Conversations (propres à chaque utilisateur) -----------------------------------

def _conv(conv_id, u):
    c = S.q("SELECT * FROM conversations WHERE id=? AND user_id=?", (conv_id, u["id"]), one=True)
    if not c:
        raise HTTPException(404, "Conversation introuvable")
    return c


@app.get("/api/conversations")
def lister_conv(u=Depends(user_dep)):
    convs = S.q("SELECT id, titre FROM conversations WHERE user_id=? ORDER BY created_at DESC", (u["id"],))
    for c in convs:
        c["messages"] = S.q("SELECT id, question, reponse, sql AS sql_genere, resultats, erreur "
                            "FROM messages WHERE conv_id=? ORDER BY id", (c["id"],))
        for m in c["messages"]:
            m["resultats"] = json.loads(m["resultats"]) if m["resultats"] else None
    return convs


class Titre(BaseModel):
    titre: str


@app.post("/api/conversations")
def creer_conv(u=Depends(user_dep)):
    cid = str(uuid.uuid4())
    S.q("INSERT INTO conversations VALUES(?,?,?,?)", (cid, u["id"], None, time.time()), write=True)
    return {"id": cid, "titre": None, "messages": []}


@app.patch("/api/conversations/{cid}")
def renommer_conv(cid: str, p: Titre, u=Depends(user_dep)):
    _conv(cid, u)
    S.q("UPDATE conversations SET titre=? WHERE id=?", (p.titre.strip()[:120], cid), write=True)
    return {"ok": True}


@app.delete("/api/conversations/{cid}")
def supprimer_conv(cid: str, u=Depends(user_dep)):
    _conv(cid, u)
    S.q("DELETE FROM conversations WHERE id=?", (cid,), write=True)
    return {"ok": True}


# --- Question en langage naturel -------------------------------------------------------

class Question(BaseModel):
    conv_id: str
    question: str
    veut_reponse: bool = True
    veut_tableau: bool = True


@app.post("/api/ask")
def ask(p: Question, u=Depends(user_dep)):
    question = p.question.strip()
    if not question:
        raise HTTPException(400, "La question ne peut pas être vide.")
    conv = _conv(p.conv_id, u)
    allowed = S.allowed_for(u)
    try:
        schema = S.schema_text(allowed)
    except Exception as e:
        raise HTTPException(500, f"Base métier inaccessible : {e}")
    if not schema:
        raise HTTPException(403, "Aucune donnée n'est accessible à votre service. Contactez un administrateur.")

    hist = []
    for m in S.q("SELECT question, reponse FROM messages WHERE conv_id=? ORDER BY id DESC LIMIT 3", (conv["id"],))[::-1]:
        hist += [MessageHistorique(role="user", content=m["question"] or ""),
                 MessageHistorique(role="assistant", content=m["reponse"] or "(Tableau généré)")]

    def enregistrer(**kw):
        if conv["titre"] is None:
            S.q("UPDATE conversations SET titre=? WHERE id=?", (question[:80], conv["id"]), write=True)
        return S.q("INSERT INTO messages(conv_id,question,reponse,sql,resultats,erreur,created_at) "
                   "VALUES(?,?,?,?,?,?,?)",
                   (conv["id"], question, kw.get("reponse"), kw.get("sql"),
                    json.dumps(kw["resultats"], default=str, ensure_ascii=False) if kw.get("resultats") else None,
                    kw.get("erreur"), time.time()), write=True)

    try:
        sql = generer_sql(question, schema, hist)
    except Exception as e:
        raise HTTPException(502, f"Erreur Gemini (génération SQL): {e}")

    t0 = time.time()
    try:
        res = S.run_query(u, sql)
    except PermissionError as e:
        S.log_query(u, question, sql, "refusé")
        enregistrer(sql=sql, erreur=str(e))
        raise HTTPException(403, str(e))
    except (ValueError, RuntimeError) as e:
        S.log_query(u, question, sql, "erreur")
        enregistrer(sql=sql, erreur=str(e))
        raise HTTPException(400, f"Requête invalide: {e}")
    S.log_query(u, question, sql, "ok", res["row_count"], int((time.time() - t0) * 1000))

    rep = ""
    if p.veut_reponse:
        try:
            rep = formuler_reponse(question, res)
        except Exception as e:
            raise HTTPException(502, f"Erreur Gemini (formulation): {e}")
    if not (p.veut_tableau or p.veut_reponse):
        p.veut_tableau = True                      # toujours afficher au moins un des deux
    if not p.veut_tableau:
        res["masque"] = True                       # tableau conservé (export) mais non affiché
    if MOTS_GRAPH.search(question):
        g = choisir_graphique(question, res)
        if g:
            res["graphique"] = g
    mid = enregistrer(reponse=rep, sql=sql, resultats=res)
    return {"id": mid, "reponse": rep, "sql_genere": sql, "resultats": res}


# --- Export d'un tableau ---------------------------------------------------------------------

def _cell(v):
    """Neutralise l'injection de formules (Excel/LibreOffice)."""
    v = "" if v is None else v
    return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


@app.get("/api/export/{mid}")
def exporter(mid: int, format: str = "csv", u=Depends(user_dep)):
    m = S.q("""SELECT m.resultats FROM messages m JOIN conversations c ON c.id=m.conv_id
               WHERE m.id=? AND c.user_id=?""", (mid, u["id"]), one=True)
    if not m or not m["resultats"]:
        raise HTTPException(404, "Aucun tableau à exporter")
    r = json.loads(m["resultats"])
    cols, rows = r["columns"], [[_cell(row.get(c)) for c in r["columns"]] for row in r["rows"]]
    nom = f"export_{mid}"
    if format in ("csv", "tsv"):
        buf = io.StringIO()
        w = csv.writer(buf, delimiter=";" if format == "csv" else "\t")  # ";" = Excel FR
        w.writerow(cols); w.writerows(rows)
        data, mime = ("\ufeff" + buf.getvalue()).encode("utf-8"), "text/csv; charset=utf-8"
    elif format == "json":
        data = json.dumps([dict(zip(cols, x)) for x in rows], ensure_ascii=False, indent=2, default=str).encode()
        mime = "application/json"
    elif format == "md":
        esc = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
        lignes = ["| " + " | ".join(map(esc, cols)) + " |", "|" + "---|" * len(cols)]
        lignes += ["| " + " | ".join(esc(v) for v in x) + " |" for x in rows]
        data, mime = "\n".join(lignes).encode(), "text/markdown; charset=utf-8"
    elif format == "pdf":
        try:
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


# --- Administration ------------------------------------------------------------------------------

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
    return S.q("""SELECT u.id, u.username, u.email, u.role, u.active, u.service_id, s.name AS service, u.created_at
                  FROM users u LEFT JOIN services s ON s.id=u.service_id ORDER BY u.username""")


@app.post("/api/admin/users")
def admin_creer_user(p: NouvelUtilisateur, _=Depends(admin_dep)):
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
    if uid == a["id"] and (p.active is False or (p.role and p.role != "admin")):
        raise HTTPException(400, "Vous ne pouvez pas retirer vos propres droits d'admin")
    d = p.model_dump(exclude_unset=True)
    if "role" in d and d["role"] not in ("admin", "user"):
        raise HTTPException(400, "Rôle invalide")
    if "password" in d:
        if len(d["password"]) < 10:
            raise HTTPException(400, "Au moins 10 caractères")
        S.q("UPDATE users SET pwd_hash=? WHERE id=?", (S.hash_pw(d.pop("password")), uid), write=True)
        S.q("DELETE FROM sessions WHERE user_id=?", (uid,), write=True)
    if "email" in d:
        try:
            S.q("UPDATE users SET email=? WHERE id=?", ((d["email"] or "").strip() or None, uid), write=True)
        except Exception:
            raise HTTPException(400, "Adresse e-mail déjà utilisée")
    for champ in ("role", "service_id", "active"):
        if champ in d:
            S.q(f"UPDATE users SET {champ}=? WHERE id=?", (int(d[champ]) if champ == "active" else d[champ], uid), write=True)
    if d.get("active") is False:
        S.q("DELETE FROM sessions WHERE user_id=?", (uid,), write=True)
    return {"ok": True}


class NomService(BaseModel):
    name: str


@app.get("/api/admin/services")
def admin_services(_=Depends(admin_dep)):
    svcs = S.q("SELECT id, name FROM services ORDER BY name")
    for s in svcs:
        s["permissions"] = [{"table": r["table_name"], "columns": json.loads(r["columns"]) if r["columns"] else None}
                            for r in S.q("SELECT table_name, columns FROM permissions WHERE service_id=?", (s["id"],))]
    return svcs


@app.post("/api/admin/services")
def admin_creer_service(p: NomService, _=Depends(admin_dep)):
    try:
        return {"id": S.q("INSERT INTO services(name) VALUES(?)", (p.name.strip(),), write=True)}
    except Exception:
        raise HTTPException(400, "Nom de service déjà utilisé")


class Droit(BaseModel):
    table: str
    columns: Optional[List[str]] = None  # None = toutes les colonnes


@app.put("/api/admin/services/{sid}/permissions")
def admin_droits(sid: int, droits: List[Droit], _=Depends(admin_dep)):
    connues = S.tables_info()
    S.q("DELETE FROM permissions WHERE service_id=?", (sid,), write=True)
    for d in droits:
        if d.table not in connues or (d.columns and not set(d.columns) <= set(connues[d.table])):
            raise HTTPException(400, f"Table ou colonne inconnue : {d.table}")
        S.q("INSERT INTO permissions VALUES(?,?,?)",
            (sid, d.table, json.dumps(d.columns) if d.columns else None), write=True)
    return {"ok": True}


@app.get("/api/admin/schema")
def admin_schema(_=Depends(admin_dep)):
    try:
        return S.tables_info()
    except Exception as e:
        raise HTTPException(500, f"Base métier inaccessible : {e}")


@app.get("/api/admin/logs")
def admin_logs(username: str = "", status: str = "", limit: int = 200, _=Depends(admin_dep)):
    return S.q("""SELECT id, username, question, sql, status, row_count, duration_ms, created_at
                  FROM query_log WHERE (?='' OR username=?) AND (?='' OR status=?)
                  ORDER BY id DESC LIMIT ?""", (username, username, status, status, min(limit, 1000)))