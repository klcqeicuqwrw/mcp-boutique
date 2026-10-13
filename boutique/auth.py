import time
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel
import securite as S
from boutique.dependencies import user_dep, COOKIE_SECURE

router = APIRouter()

class Login(BaseModel):
    username: str
    password: str

@router.post("/api/login")
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

@router.post("/api/logout")
def logout(request: Request, response: Response):
    """Déconnecte l'utilisateur en invalidant son token côté serveur et côté navigateur."""
    if request.cookies.get("session"):
        S.logout(request.cookies["session"])
    response.delete_cookie("session")
    return {"ok": True}

@router.get("/api/me")
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

@router.post("/api/mdp-oublie")
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

@router.post("/api/reinit")
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

@router.post("/api/password")
def changer_mdp(p: Mdp, u=Depends(user_dep)):
    """Permet à un utilisateur connecté de modifier son mot de passe."""
    if not S.check_pw(p.ancien, u["pwd_hash"]):
        raise HTTPException(400, "Ancien mot de passe incorrect")
    if len(p.nouveau) < 10:
        raise HTTPException(400, "Au moins 10 caractères")
    S.q("UPDATE users SET pwd_hash=? WHERE id=?", (S.hash_pw(p.nouveau), u["id"]), write=True)
    return {"ok": True}


# --- API : Conversations (propres à chaque utilisateur) -------------------------

