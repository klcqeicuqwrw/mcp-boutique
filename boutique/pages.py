import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
import securite as S
from boutique.dependencies import user_dep, WEB

router = APIRouter()

def _user_or_none(request: Request):
    """Fonction utilitaire pour récupérer l'utilisateur sans déclencher d'erreur s'il n'est pas connecté."""
    return S.user_from_token(request.cookies.get("session"))

@router.get("/")
def accueil(request: Request):
    """Route principale (Racine). Redirige vers le Chat, l'Admin ou le Login selon l'état."""
    u = _user_or_none(request)
    if not u:
        # Non connecté -> Affiche la page de connexion sans la mettre en cache
        return FileResponse(WEB / "login.html", headers={"Cache-Control": "no-store"})
    # Connecté -> Redirection selon le rôle
    return RedirectResponse("/admin" if u["role"] == "admin" else "/chat")

@router.get("/reinit")
def page_reinit():
    """Page permettant de réinitialiser son mot de passe depuis un lien email."""
    return FileResponse(WEB / "reset.html")

@router.get("/chat")
def page_chat(request: Request):
    """Page contenant l'interface de conversation (Le Chatbot)."""
    if not _user_or_none(request):
        return RedirectResponse("/")
    return FileResponse(WEB / "index.html")

@router.get("/admin")
def page_admin(request: Request):
    """Page d'administration (gestion utilisateurs, logs, droits)."""
    u = _user_or_none(request)
    if not u:
        return RedirectResponse("/")
    if u["role"] != "admin":
        return RedirectResponse("/chat")
    return FileResponse(WEB / "admin.html")


# --- Carte du patrimoine ---------------------------------------------------------

@router.get("/carte")
def page_carte(request: Request):
    """Page de la carte du patrimoine (Leaflet). Même contrôle de session que /chat."""
    if not _user_or_none(request):
        return RedirectResponse("/")
    return FileResponse(WEB / "carte.html", headers={"Cache-Control": "no-store"})


def _coord(valeur, borne):
    """Convertit '48,1173' ou '48.1173' (texte) en nombre ; None si vide, invalide ou hors bornes."""
    try:
        x = float(str(valeur).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    return x if -borne <= x <= borne else None


@router.get("/api/carte")
def api_carte(response: Response, u=Depends(user_dep)):
    """Points du patrimoine pour la carte. Passe par run_query : les droits du service s'appliquent.
    Les adresses (données RGPD) ne sont volontairement jamais lues ni renvoyées."""
    sql = ("SELECT ID_patrimoine AS id, Libelle_patrimoine AS type_patrimoine, Libelle_commune AS ville, Latitude AS latitude, Longitude AS longitude "
           "FROM patrimoine "
           "WHERE latitude IS NOT NULL AND TRIM(latitude) <> '' AND longitude IS NOT NULL AND TRIM(longitude) <> ''")
    t0 = time.time()
    try:
        res = S.run_query(u, sql, max_rows=20000)
    except PermissionError as e:
        S.log_query(u, "[carte]", sql, "refusé")
        raise HTTPException(403, str(e))
    except (ValueError, RuntimeError) as e:
        S.log_query(u, "[carte]", sql, "erreur")
        raise HTTPException(400, f"Carte indisponible : {e}")
    S.log_query(u, "[carte]", sql, "ok", res["row_count"], int((time.time() - t0) * 1000))

    points = []
    for r in res["rows"]:
        lat, lon = _coord(r["latitude"], 90), _coord(r["longitude"], 180)
        if lat is None or lon is None or (lat == 0 and lon == 0):
            continue  # coordonnée absente, illisible ou « 0,0 »
        points.append({"id": r["id"], "nom": r["type_patrimoine"], "commune": r["ville"],
                        "lat": lat, "lon": lon})
    response.headers["Cache-Control"] = "no-store"
    return {"points": points, "ignores": res["row_count"] - len(points), "tronque": res["truncated"]}


# --- API : Authentification et Profil --------------------------------------------

