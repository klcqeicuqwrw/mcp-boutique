"""Outils collaborateurs, sans IA, avec les mêmes droits que les requêtes du chat."""
from datetime import date, timedelta
import time
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, field_validator
import securite as S
from boutique.dependencies import user_dep

router = APIRouter(prefix="/api/espace")

ENTITES = {
    "client": ("Client", "ID_client", "Client"),
    "lot": ("Lot", "ID_lot", "Logement"),
    "patrimoine": ("Patrimoine", "ID_patrimoine", "Résidence"),
    "commande": ("Commande", "ID_commande", "Commande"),
    "affaire": ("Affaire", "ID_Affaire", "Affaire"),
    "diagnostic": ("Diagnostic", "ID_diagnostic", "Diagnostic"),
    "occupant": ("Occupant", "ID_occupant", "Occupant"),
    "copropriete": ("Copropriete", "ID_copropriete", "Copropriété"),
}


class Lecture:
    def __init__(self, user):
        self.user, self.scope = user, S.access_scope(user)
        droits = S.allowed_for(user)
        self.schema = {t: [c for c in cols if droits is None or
                              (t.lower() in droits and (droits[t.lower()] is None or c.lower() in droits[t.lower()]))]
                       for t, cols in S.tables_info().items()}

    def permet(self, table, *colonnes):
        return bool(self.schema.get(table)) and set(colonnes) <= set(self.schema[table])

    def requete(self, sql, args=(), limite=100):
        try:
            return S.run_query(self.user, sql, max_rows=limite, args=args)
        except PermissionError as exc:
            raise HTTPException(403, "Vos droits ne permettent pas de consulter ces informations.") from exc
        except RuntimeError as exc:
            raise HTTPException(503, "Ces données ne sont pas accessibles pour le moment.") from exc

    def lire(self, table, condition, args=(), requis=(), ordre=""):
        if not self.permet(table, *requis):
            return None
        colonnes = ','.join('"' + c.replace('"', '""') + '"' for c in self.schema[table])
        return self.requete(f'SELECT DISTINCT {colonnes} FROM "{table}" WHERE {condition}' +
                            (f' ORDER BY {ordre}' if ordre else ''), args)

    def terminer(self, valeur):
        if not S.scope_actuel(self.user, self.scope):
            raise HTTPException(403, "Vos droits ont changé. Actualisez la page.")
        return valeur


def racine(lecture, type_entite, identifiant):
    if type_entite not in ENTITES:
        raise HTTPException(404, "Type de fiche inconnu.")
    table, cle, titre = ENTITES[type_entite]
    if not lecture.permet(table, cle):
        raise HTTPException(403, "Cette fiche n'est pas accessible à votre service.")
    resultat = lecture.lire(table, f'"{cle}"=?', (identifiant,), (cle,))
    if not resultat["rows"]:
        raise HTTPException(404, "Fiche introuvable.")
    return table, titre, resultat


@router.get("/fiche/{type_entite}")
def fiche(type_entite: str, identifiant: str = Query(min_length=1, max_length=200), u=Depends(user_dep)):
    lecture = Lecture(u)
    table, titre, resultat = racine(lecture, type_entite, identifiant)
    sections = [dict(titre=titre, table=table, resultats=resultat)]

    def ajouter(libelle, cible, colonne, valeurs, ordre=""):
        valeurs = list(dict.fromkeys(v for v in valeurs if v is not None and v != ''))
        if not valeurs or not lecture.permet(cible, colonne):
            return
        cond = f'"{colonne}" IN ({",".join("?" for _ in valeurs)})'
        res = lecture.lire(cible, cond, valeurs, (colonne,), ordre)
        if res is not None:
            sections.append(dict(titre=libelle, table=cible, resultats=res))

    def valeurs(colonne):
        return [r.get(colonne) for r in resultat["rows"]]

    def client_sections(ids):
        ajouter("Occupants et contacts", "Occupant", "ID_client", ids)
        ajouter("Baux et préavis", "Bail", "ID_client", ids)
        ajouter("Affaires", "Affaire", "ID_client_demandeur_affaire", ids)
        for cible, libelle in [("Releve_compte_client_historique", "Compte client — historique mensuel"),
                               ("Contentieux_client_historique", "Procédures — historique mensuel")]:
            ordre = '"Annee_mois" DESC' if lecture.permet(cible, "Annee_mois") else ''
            ajouter(libelle, cible, "ID_client", ids, ordre)

    if type_entite == "client":
        client_sections([identifiant])
        if lecture.permet("Client_lot_pivot", "ID_client", "ID_lot"):
            liens = lecture.lire("Client_lot_pivot", '"ID_client"=?', (identifiant,), ("ID_client", "ID_lot"))
            if liens["truncated"]:
                sections.append(dict(titre="Rattachements aux lots (liste limitée)", table="Client_lot_pivot", resultats=liens))
            ajouter("Logements", "Lot", "ID_lot", [r["ID_lot"] for r in liens["rows"]])
    elif type_entite == "lot":
        ajouter("Résidence et itinéraire", "Patrimoine", "ID_patrimoine", valeurs("ID_patrimoine"))
        for cible, libelle in [("Bail", "Baux et préavis"), ("Affaire", "Affaires"), ("Diagnostic", "Diagnostics")]:
            ajouter(libelle, cible, "ID_lot", [identifiant])
        if lecture.permet("Client_lot_pivot", "ID_lot", "ID_client"):
            liens = lecture.lire("Client_lot_pivot", '"ID_lot"=?', (identifiant,), ("ID_lot", "ID_client"))
            ids = [r["ID_client"] for r in liens["rows"]]
            ajouter("Clients", "Client", "ID_client", ids)
            ajouter("Occupants et contacts", "Occupant", "ID_client", ids)
        if lecture.permet("Equipement", "Code_societe", "Code_lot"):
            for r in resultat["rows"][:1]:
                if r.get("Code_societe") and r.get("Code_lot"):
                    res = lecture.lire("Equipement", '"Code_societe"=? AND "Code_lot"=?',
                                       (r["Code_societe"], r["Code_lot"]), ("Code_societe", "Code_lot"))
                    sections.append(dict(titre="Équipements", table="Equipement", resultats=res))
    elif type_entite == "commande":
        ajouter("Interventions", "Intervention", "ID_commande", [identifiant])
    elif type_entite == "affaire":
        ajouter("Client demandeur", "Client", "ID_client", valeurs("ID_client_demandeur_affaire"))
        ajouter("Logement", "Lot", "ID_lot", valeurs("ID_lot"))
        ajouter("Résidence", "Patrimoine", "ID_patrimoine", valeurs("ID_patrimoine"))
    elif type_entite == "patrimoine":
        ajouter("Logements", "Lot", "ID_patrimoine", [identifiant])
        ajouter("Copropriétés et syndic", "Copropriete", "ID_patrimoine", [identifiant])
    elif type_entite == "occupant":
        ajouter("Client", "Client", "ID_client", valeurs("ID_client"))
    elif type_entite == "diagnostic":
        ajouter("Valeurs du diagnostic", "Diagnostic_valeur", "ID_diagnostic", [identifiant])
        ajouter("Logement", "Lot", "ID_lot", valeurs("ID_lot"))
    elif type_entite == "copropriete":
        ajouter("Résidence", "Patrimoine", "ID_patrimoine", valeurs("ID_patrimoine"))

    codes = []
    for r in resultat["rows"]:
        for col in ("Code_collaborateur_suivi", "Code_collaborateur_execution", "Code_collaborateur_enregistrement", "Code_collaborateur_executant_commande"):
            if r.get(col):
                codes.append(r[col])
    ajouter("Collaborateurs responsables", "Collaborateur", "Code_collaborateur", codes)
    return lecture.terminer(dict(titre=titre, identifiant=identifiant, sections=sections))


@router.get("/itineraire/{type_entite}", include_in_schema=False)
@router.get("/carte/{type_entite}")
def carte_fiche(type_entite: str, identifiant: str = Query(min_length=1, max_length=200), u=Depends(user_dep)):
    lecture = Lecture(u)
    racine(lecture, type_entite, identifiant)
    lecture.terminer(None)
    return RedirectResponse('/carte?' + urlencode(dict(type_entite=type_entite, identifiant=identifiant)))


def categories(au):
    horizon = (au + timedelta(days=90)).isoformat()
    jour = au.isoformat()
    return {
        "affaires": dict(titre="Affaires en retard", table="Affaire", cle="ID_Affaire",
            requis=("Indicateur_statut_etat_affaire", "Date_theorique_cloture"),
            condition='"Indicateur_statut_etat_affaire"=\'Ouvert\' AND date("Date_theorique_cloture") < date(?)', args=(jour,),
            description="Affaires ouvertes dont la date théorique de clôture est dépassée."),
        "commandes": dict(titre="Commandes à relancer", table="Commande", cle="ID_commande",
            requis=("Taux_execution_commande", "Date_fin_execution_commande"),
            condition='"Taux_execution_commande" < 100 AND date("Date_fin_execution_commande") < date(?)', args=(jour,),
            description="Commandes exécutées à moins de 100 % dont la fin prévue est dépassée."),
        "diagnostics": dict(titre="Diagnostics à renouveler", table="Diagnostic", cle="ID_diagnostic",
            requis=("Indicateur_diagnostic_le_plus_recent", "Date_fin_diagnostic"),
            condition='"Indicateur_diagnostic_le_plus_recent"=\'Oui\' AND date("Date_fin_diagnostic") <= date(?)', args=(horizon,),
            description="Derniers diagnostics arrivés à échéance ou expirant sous 90 jours."),
        "departs": dict(titre="Préavis à préparer", table="Bail", cle="ID_bail",
            requis=("Indicateur_occupation_active", "Date_reception_preavis"),
            condition='"Indicateur_occupation_active"=\'Actif\' AND date("Date_reception_preavis") <= date(?) AND substr("Date_reception_preavis",1,4) < \'2090\'', args=(jour,),
            description="Baux encore actifs avec un préavis reçu ; les dates sentinelles sont exclues."),
        "mandats": dict(titre="Mandats de syndic", table="Copropriete", cle="ID_copropriete",
            requis=("Etat_mandat_copropriete", "Date_fin_mandat_copropriete"),
            condition='("Etat_mandat_copropriete"=\'Mandat en cours\' AND date("Date_fin_mandat_copropriete") <= date(?)) OR "Etat_mandat_copropriete"=\'Mandat expiré sans successeur déclaré\'', args=(horizon,),
            description="Mandats en cours expirant sous 90 jours ou déclarés expirés sans successeur."),
        "comptes": dict(titre="Comptes à examiner", table="Releve_compte_client_historique", cle="ID_client",
            requis=("Montant_impaye", "Annee_mois"),
            condition='"Montant_impaye">0 AND "Annee_mois"=(SELECT MAX(h."Annee_mois") FROM "Releve_compte_client_historique" h WHERE h."ID_client"="Releve_compte_client_historique"."ID_client" AND date(h."Annee_mois") <= date(?))', args=(jour,),
            description="Clients avec un impayé sur leur dernier mois disponible à la date choisie ; aucune relance automatique."),
    }


@router.get("/a-traiter")
def a_traiter(categorie: str | None = None, au: date | None = None, u=Depends(user_dep)):
    # Date métier explicite, indépendante du fuseau du serveur Windows.
    if au is None:
        raise HTTPException(422, "Indiquez une date de référence (au=AAAA-MM-JJ).")
    lecture = Lecture(u)
    choix = categories(au)
    if categorie and categorie not in choix:
        raise HTTPException(404, "Catégorie inconnue.")
    cartes = []
    for code, definition in choix.items():
        if categorie and categorie != code:
            continue
        t, cle = definition["table"], definition["cle"]
        carte = dict(code=code, titre=definition["titre"], description=definition["description"], disponible=False)
        if lecture.permet(t, cle, *definition["requis"]):
            condition, args = definition["condition"], definition["args"]
            total = lecture.requete(f'SELECT COUNT(DISTINCT "{cle}") AS nombre FROM "{t}" WHERE {condition}', args)["rows"][0]["nombre"]
            carte.update(disponible=True, total=total)
            if lecture.permet(t, "Date_actualisation"):
                carte["actualisation"] = lecture.requete(f'SELECT MAX("Date_actualisation") AS derniere FROM "{t}"')["rows"][0]["derniere"]
            if categorie:
                carte["resultats"] = lecture.lire(t, condition, args, (cle, *definition["requis"]), f'"{cle}"')
        cartes.append(carte)
    return lecture.terminer(dict(au=au.isoformat(), cartes=cartes))


class Favori(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1, max_length=8000)

    @field_validator('label', 'question')
    @classmethod
    def nettoyer(cls, valeur):
        if not valeur.strip():
            raise ValueError("Saisissez un texte non vide.")
        return valeur.strip()


@router.get("/favoris")
def favoris(u=Depends(user_dep)):
    return S.q('SELECT id,label,question FROM favorite_searches WHERE user_id=? ORDER BY created_at DESC', (u["id"],))


@router.post("/favoris")
def sauver_favori(p: Favori, u=Depends(user_dep)):
    existant = S.q('SELECT id FROM favorite_searches WHERE user_id=? AND question=?', (u["id"], p.question), one=True)
    if not existant and S.q('SELECT COUNT(*) AS n FROM favorite_searches WHERE user_id=?', (u["id"],), one=True)["n"] >= 50:
        raise HTTPException(409, "Vous avez atteint la limite de 50 recherches favorites.")
    S.q('INSERT INTO favorite_searches(user_id,label,question,created_at) VALUES(?,?,?,?) '
        'ON CONFLICT(user_id,question) DO UPDATE SET label=excluded.label', (u["id"], p.label, p.question, time.time()), write=True)
    return {"ok": True}


@router.delete("/favoris/{fid}")
def supprimer_favori(fid: int, u=Depends(user_dep)):
    if not S.q('SELECT 1 FROM favorite_searches WHERE id=? AND user_id=?', (fid, u["id"]), one=True):
        raise HTTPException(404, "Favori introuvable.")
    S.q('DELETE FROM favorite_searches WHERE id=? AND user_id=?', (fid, u["id"]), write=True)
    return {"ok": True}
