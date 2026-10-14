import json, re, time, uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import securite as S
from boutique.dependencies import user_dep

router = APIRouter()

from api import MessageHistorique, formuler_reponse, generer_sql, DICTIONNAIRE_PATH
from dictionnaire import contexte_dictionnaire
from boutique.graphiques import choisir_graphique
from boutique.requetes_rapides import sql_comptage
from boutique import localisation

MOTS_GRAPH = re.compile(r"graph|courbe|histogramme|camembert|diagramme|chart|plot", re.I)

def _conv(conv_id, u):
    """Vérifie qu'une conversation existe ET qu'elle appartient bien à l'utilisateur connecté."""
    c = S.q("SELECT * FROM conversations WHERE id=? AND user_id=?", (conv_id, u["id"]), one=True)
    if not c:
        raise HTTPException(404, "Conversation introuvable")
    return c

@router.get("/api/conversations")
def lister_conv(u=Depends(user_dep)):
    """Renvoie la liste des conversations de l'utilisateur pour construire la barre latérale."""
    return S.q("""SELECT c.id, c.titre,
                         (SELECT group_concat(question, char(10)) FROM messages WHERE conv_id=c.id) AS questions
                  FROM conversations c WHERE c.user_id=? ORDER BY c.created_at DESC""", (u["id"],))

@router.get("/api/conversations/{cid}")
def lire_conv(cid: str, u=Depends(user_dep)):
    """Charge l'historique complet des messages pour une conversation donnée."""
    _conv(cid, u)
    msgs = S.q("SELECT id, question, reponse, sql AS sql_genere, resultats, erreur, access_scope "
               "FROM messages WHERE conv_id=? ORDER BY id", (cid,))
    for m in msgs:
        if not S.message_accessible(m, u):
            m.update(reponse=None, sql_genere=None, resultats=None,
                     erreur="Résultat masqué : vos droits actuels ne permettent pas de le consulter.")
        else:
            try:
                m["resultats"] = S.lire_resultats(m["resultats"]) if m["resultats"] else None
            except ValueError as exc:
                m.update(resultats=None, erreur=str(exc))
        m.pop("access_scope", None)
    return {"messages": msgs}

class Titre(BaseModel):
    titre: str

@router.post("/api/conversations")
def creer_conv(u=Depends(user_dep)):
    """Crée une nouvelle conversation vide."""
    cid = str(uuid.uuid4())
    S.q("INSERT INTO conversations VALUES(?,?,?,?)", (cid, u["id"], None, time.time()), write=True)
    return {"id": cid, "titre": None, "messages": []}

@router.patch("/api/conversations/{cid}")
def renommer_conv(cid: str, p: Titre, u=Depends(user_dep)):
    """Change le nom affiché d'une conversation dans l'historique."""
    _conv(cid, u)
    S.q("UPDATE conversations SET titre=? WHERE id=?", (p.titre.strip()[:120], cid), write=True)
    return {"ok": True}

@router.delete("/api/conversations/{cid}")
def supprimer_conv(cid: str, u=Depends(user_dep)):
    """Supprime définitivement une conversation."""
    _conv(cid, u)
    S.q("DELETE FROM conversations WHERE id=?", (cid,), write=True)
    return {"ok": True}


# --- API : Question en langage naturel (Le Chatbot) ----------------------------

class Question(BaseModel):
    conv_id: str
    fournisseur: Literal["gemini", "openai"] = "gemini"
    question: str = Field(min_length=1, max_length=8000)
    veut_reponse: bool = True
    veut_tableau: bool = True

# Cache en mémoire : évite de redemander le même SQL à Gemini si la question est identique
_sql_cache: dict = {}
SQL_CACHE_TTL, SQL_CACHE_MAX = 600, 200 # Valide 10 min, max 200 requêtes en mémoire

@router.post("/api/ask")
def ask(p: Question, u=Depends(user_dep)):
    """
    Le cœur métier de l'application. Reçoit la question, filtre selon les droits,
    demande la requête SQL à Gemini, et l'exécute sur la base.
    """
    question = p.question.strip()
    if not question:
        raise HTTPException(400, "La question ne peut pas être vide.")
    conv = _conv(p.conv_id, u)
    scope = S.access_scope(u)
    if localisation.reprise(question):
        precedent = S.q("SELECT sql,resultats,access_scope FROM messages WHERE conv_id=? AND resultats IS NOT NULL ORDER BY id DESC LIMIT 1", (conv["id"],), one=True)
        if not precedent:
            raise HTTPException(400, "Demandez d'abord une liste de résultats à localiser.")
        if not S.message_accessible(precedent, u):
            raise HTTPException(403, "Vos droits ne permettent plus de consulter ces résultats.")
        try:
            res = S.lire_resultats(precedent["resultats"])
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if not localisation.possible(res):
            raise HTTPException(400, "Cette sélection ne contient pas d'identifiant de logement, patrimoine, client ou occupant pour la carte.")
        res["localisation_demandee"] = True
        res.pop("masque", None)
        rep = "La sélection est prête à être affichée sur la carte."
        mid = S.q("INSERT INTO messages(conv_id,question,reponse,sql,resultats,created_at,access_scope) VALUES(?,?,?,?,?,?,?)",
                  (conv["id"], question, rep, precedent["sql"], json.dumps(res, ensure_ascii=False), time.time(), scope), write=True)
        if not S.scope_actuel(u, scope):
            raise HTTPException(403, "Vos droits ont changé pendant la demande.")
        S.log_query(u, question, precedent["sql"], "ok", res["row_count"])
        return dict(id=mid, reponse=rep, sql_genere=precedent["sql"], resultats=res, texte_en_attente=False)
    
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
    for m in S.q("SELECT question, reponse, sql, resultats, access_scope FROM messages WHERE conv_id=? ORDER BY id DESC LIMIT 3", (conv["id"],))[::-1]:
        if not S.message_accessible(m, u):
            continue
        hist += [MessageHistorique(role="user", content=m["question"] or ""),
                 MessageHistorique(role="assistant", content=(m["reponse"] or "(Tableau généré)")
                                  + ("\nRequête précédente : " + m["sql"] if m["sql"] else ""))]

    def enregistrer(**kw):
        """Sous-fonction pour sauvegarder l'échange dans la base de données."""
        if conv["titre"] is None:
            # Nomme automatiquement la conversation avec la première question posée
            S.q("UPDATE conversations SET titre=? WHERE id=?", (question[:80], conv["id"]), write=True)
        return S.q("INSERT INTO messages(conv_id,question,reponse,sql,resultats,erreur,created_at,access_scope) "
                   "VALUES(?,?,?,?,?,?,?,?)",
                   (conv["id"], question, kw.get("reponse"), kw.get("sql"),
                    json.dumps(kw["resultats"], default=str, ensure_ascii=False) if kw.get("resultats") else None,
                    kw.get("erreur"), time.time(), scope), write=True)

    # 3. Génération du SQL par l'IA (ou utilisation du Cache)
    infos = S.tables_info()
    schema_autorise = {t.lower(): {c.lower() for c in colonnes
                         if allowed is None or allowed[t.lower()] is None or c.lower() in allowed[t.lower()]}
                      for t, colonnes in infos.items() if allowed is None or t.lower() in allowed}
    rapide = sql_comptage(question, schema_autorise) if not hist else None
    dictionnaire = "" if rapide else contexte_dictionnaire(DICTIONNAIRE_PATH, schema_autorise, question)
    cle = (question, schema, dictionnaire, p.fournisseur)
    en_cache = None if hist else _sql_cache.get(cle)
    journal = lambda **kw: S.log_gemini(u, conv["id"], **kw)
    fournisseur, erreur_primaire, res = p.fournisseur, None, None
    sql = None
    if rapide:
        sql, fournisseur = rapide, "local"
    elif en_cache and time.time() - en_cache[0] < SQL_CACHE_TTL:
        sql = en_cache[1]
        fournisseur = en_cache[2] if len(en_cache) > 2 else "gemini"
    else:
        try:
            sql = generer_sql(question, schema, hist, log=journal, dictionnaire=dictionnaire, fournisseur=p.fournisseur)
        except Exception as exc:
            erreur_primaire = exc

    def verifier_droits():
        if not S.scope_actuel(u, scope):
            raise HTTPException(403, "Vos droits ont changé pendant la demande. Reposez la question.")

    def refus(sql_refuse, exc):
        S.log_query(u, question, sql_refuse, "refusé")
        enregistrer(sql=sql_refuse, erreur=str(exc))
        raise HTTPException(403, str(exc)) from exc

    t0 = time.time()
    if sql is not None:
        verifier_droits()
        try:
            res = S.run_query(u, sql)
        except PermissionError as exc:
            refus(sql, exc)  # Un refus de droits ne déclenche jamais un autre fournisseur.
        except (ValueError, RuntimeError) as exc:
            erreur_primaire = exc
            _sql_cache.pop(cle, None)
            S.log_query(u, question, sql, "erreur")

    if erreur_primaire is not None:
        nom = "OpenAI" if p.fournisseur == "openai" else "Gemini"
        erreur = f"{nom} n'a pas pu répondre. Vérifiez sa clé API et sa disponibilité, puis réessayez."
        enregistrer(sql=sql, erreur=erreur)
        raise HTTPException(502, erreur) from erreur_primaire

    verifier_droits()
    res["fournisseur_sql"] = fournisseur
    res["fournisseur_ia"] = p.fournisseur
    S.log_query(u, question, sql, "ok", res["row_count"], int((time.time() - t0) * 1000))
    if not hist:
        if len(_sql_cache) >= SQL_CACHE_MAX:
            _sql_cache.clear()
        _sql_cache[cle] = (time.time(), sql, fournisseur)

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
    res["localisation_demandee"] = localisation.demandee(question) and localisation.possible(res)
    mid = enregistrer(reponse=rep, sql=sql, resultats=res)
    if not S.scope_actuel(u, scope):
        raise HTTPException(403, "Vos droits ont changé pendant la demande. Reposez la question.")
    return {"id": mid, "reponse": rep, "sql_genere": sql, "resultats": res, "texte_en_attente": attente}

@router.post("/api/ask/{mid}/texte")
def ask_texte(mid: int, u=Depends(user_dep)):
    """
    Seconde étape (asynchrone du point de vue de l'utilisateur) : 
    Demande à Gemini de formuler une réponse en Français à partir du tableau de résultats.
    """
    m = S.q("""SELECT m.question, m.reponse, m.resultats, m.sql, m.access_scope FROM messages m
               JOIN conversations c ON c.id=m.conv_id WHERE m.id=? AND c.user_id=?""", (mid, u["id"]), one=True)
    if not m or not m["resultats"]:
        raise HTTPException(404, "Message introuvable")
    if not S.message_accessible(m, u):
        raise HTTPException(403, "Vos droits actuels ne permettent pas de consulter ce résultat.")
    if m["reponse"]:
        return {"reponse": m["reponse"]} # Déjà générée
        
    conv_id = S.q("SELECT conv_id FROM messages WHERE id=?", (mid,), one=True)["conv_id"]
    journal = lambda **kw: S.log_gemini(u, conv_id, **kw)
    scope = S.access_scope(u)
    try:
        resultats = S.lire_resultats(m["resultats"])
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    try:
        rep = formuler_reponse(m["question"], resultats, log=journal, sql=m["sql"])
    except Exception as e:
        raise HTTPException(502, "La synthèse IA est temporairement indisponible. Le tableau reste accessible.")
    if not S.scope_actuel(u, scope):
        raise HTTPException(403, "Vos droits ont changé pendant la demande. Reposez la question.")
        
    S.q("UPDATE messages SET reponse=? WHERE id=?", (rep, mid), write=True)
    return {"reponse": rep}


# --- API : Export d'un tableau (CSV, PDF, Excel...) -----------------------------

