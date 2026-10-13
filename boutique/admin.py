import json, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import securite as S
from boutique.dependencies import admin_dep

router = APIRouter()

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

@router.get("/api/admin/users")
def admin_users(_=Depends(admin_dep)):
    """Liste tous les utilisateurs, leur statut et leur service (département)."""
    return S.q("""SELECT u.id, u.username, u.email, u.role, u.active, u.service_id, s.name AS service, u.created_at
                  FROM users u LEFT JOIN services s ON s.id=u.service_id ORDER BY u.username""")

@router.post("/api/admin/users")
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

@router.patch("/api/admin/users/{uid}")
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

@router.get("/api/admin/services")
def admin_services(_=Depends(admin_dep)):
    """Renvoie la liste des services avec leurs permissions respectives par table."""
    svcs = S.q("SELECT id, name FROM services ORDER BY name")
    for s in svcs:
        s["permissions"] = [{"table": r["table_name"], "columns": json.loads(r["columns"]) if r["columns"] else None}
                            for r in S.q("SELECT table_name, columns FROM permissions WHERE service_id=?", (s["id"],))]
    return svcs

@router.post("/api/admin/services")
def admin_creer_service(p: NomService, _=Depends(admin_dep)):
    """Ajoute un nouveau service (ex: RH, Marketing, Comptabilité)."""
    try:
        return {"id": S.q("INSERT INTO services(name) VALUES(?)", (p.name.strip(),), write=True)}
    except Exception:
        raise HTTPException(400, "Nom de service déjà utilisé")

class Droit(BaseModel):
    table: str
    columns: Optional[List[str]] = None  # Si None, l'utilisateur a accès à toutes les colonnes de la table

@router.put("/api/admin/services/{sid}/permissions")
def admin_droits(sid: int, droits: List[Droit], _=Depends(admin_dep)):
    """Remplace l'ensemble des droits d'accès aux tables pour un service donné."""
    try:
        S.remplacer_permissions(sid, droits)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}

@router.get("/api/admin/schema")
def admin_schema(_=Depends(admin_dep)):
    """Affiche le schéma complet de la base de données (pour configurer les droits)."""
    try:
        return S.tables_info()
    except Exception as e:
        raise HTTPException(500, f"Base métier inaccessible : {e}")

@router.get("/api/admin/logs")
def admin_logs(username: str = "", status: str = "", limit: int = 200, _=Depends(admin_dep)):
    """Journal de toutes les requêtes SQL effectuées sur l'application."""
    return S.q("""SELECT id, username, question, sql, status, row_count, duration_ms, created_at
                  FROM query_log WHERE (?='' OR username=?) AND (?='' OR status=?)
                  ORDER BY id DESC LIMIT ?""", (username, username, status, status, min(limit, 1000)))

@router.get("/api/admin/gemini-logs")
def admin_gemini_logs(username: str = "", kind: str = "", limit: int = 200, _=Depends(admin_dep)):
    """Journal technique des échanges avec l'IA Gemini (pour traquer les coûts et les erreurs de prompt)."""
    return S.q("""SELECT id, username, conv_id, kind, model, system_instruction, prompt, reponse,
                         prompt_tokens, response_tokens, total_tokens, duration_ms, erreur, created_at
                  FROM gemini_log WHERE (?='' OR username=?) AND (?='' OR kind=?)
                  ORDER BY id DESC LIMIT ?""", (username, username, kind, kind, min(limit, 1000)))

@router.get("/api/admin/gemini-logs/stats")
def admin_gemini_stats(_=Depends(admin_dep)):
    """Retourne les statistiques de consommation (Tokens) de l'API Google Gemini."""
    jour, semaine = time.time() - 86400, time.time() - 7 * 86400
    def total(depuis):
        r = S.q("SELECT COUNT(*) n, COALESCE(SUM(total_tokens),0) t FROM gemini_log WHERE created_at>=?",
                (depuis,), one=True)
        return {"echanges": r["n"], "tokens": r["t"]}
    return {"jour": total(jour), "semaine": total(semaine), "total": total(0)}