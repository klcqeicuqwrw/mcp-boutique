import os
from fastapi import Depends, HTTPException, Request
import config
import securite as S

WEB = config.ROOT / "web"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"

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

