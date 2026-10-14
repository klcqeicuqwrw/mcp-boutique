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
def api_carte(response: Response, message_id: int | None = None, u=Depends(user_dep)):
    """Points du patrimoine pour la carte. Passe par run_query : les droits du service s'appliquent.
    Les adresses (données RGPD) ne sont volontairement jamais lues ni renvoyées."""
    sql = ("SELECT ID_patrimoine AS id, Libelle_patrimoine AS type_patrimoine, Libelle_commune AS ville, Latitude AS latitude, Longitude AS longitude "
           "FROM patrimoine "
           "WHERE latitude IS NOT NULL AND TRIM(latitude) <> '' AND longitude IS NOT NULL AND TRIM(longitude) <> ''")
    args = ()
    if message_id is not None:
        m = S.q("SELECT m.sql,m.resultats,m.access_scope FROM messages m JOIN conversations c ON c.id=m.conv_id WHERE m.id=? AND c.user_id=?", (message_id, u["id"]), one=True)
        if not m:
            raise HTTPException(404, "Résultat introuvable")
        if not S.message_accessible(m, u):
            raise HTTPException(403, "Vos droits ne permettent pas de consulter ce résultat.")
        try:
            resultat = S.lire_resultats(m["resultats"])
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        ids, identifiant = [], None
        for candidat in ("id_patrimoine", "id_lot", "id_client", "id_occupant"):
            colonnes = [c for c in resultat["columns"] if c.lower() == candidat]
            ids = sorted({ident.strip() for row in resultat["rows"] for col in colonnes
                          for ident in str(row.get(col) or "").split(",") if ident.strip()})
            if ids:
                identifiant = candidat
                break
        if not ids:
            return {"points": [], "ignores": 0, "tronque": False, "filtre": True}
        # Les identifiants proviennent du résultat autorisé ; paramètres SQL, jamais concaténés.
        parametres = ",".join("?" for _ in ids)
        resolutions = {
            "id_patrimoine": parametres,
            "id_lot": f"SELECT ID_patrimoine FROM Lot WHERE ID_lot IN ({parametres})",
            "id_client": f"SELECT l.ID_patrimoine FROM Lot l JOIN Client_lot_pivot cl ON cl.ID_lot=l.ID_lot WHERE cl.ID_client IN ({parametres})",
            "id_occupant": f"SELECT l.ID_patrimoine FROM Lot l JOIN Client_lot_pivot cl ON cl.ID_lot=l.ID_lot JOIN Occupant o ON o.ID_client=cl.ID_client WHERE o.ID_occupant IN ({parametres})",
        }
        sql += " AND ID_patrimoine IN (" + resolutions[identifiant] + ")"
        args = tuple(ids)
    t0 = time.time()
    try:
        res = S.run_query(u, sql, max_rows=20000, args=args)
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
    return {"points": points, "ignores": res["row_count"] - len(points), "tronque": res["truncated"], "filtre": message_id is not None}


# --- API : Authentification et Profil --------------------------------------------

