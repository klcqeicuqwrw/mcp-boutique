"""Recherches métier reconnues strictement, calculées en SQLite sans appel IA.

Les filtres sont persistés avec le résultat pour les relances de conversation.
Une formulation contenant d'autres critères reste confiée au fournisseur choisi.
"""
from dataclasses import dataclass, field
import re

from boutique.localisation import normaliser


@dataclass
class Recherche:
    sql: str | None = None
    reponse: str | None = None
    contexte: dict = field(default_factory=dict)
    note: str = ""


DEMANDE = r"(?:(?:donne(?:s|z)?|affiche(?:z)?|montre(?:z)?)(?: moi)? |liste(?:z)?(?: moi)? )?"
LISTE = DEMANDE + r"(?:la liste (?:des|de) |les )?"
PARMI = r"parmi (?:ces gens la|ces personnes|ces occupants) "


def _exiger(schema, requis):
    for table, colonnes in requis.items():
        if not set(c.lower() for c in colonnes) <= schema.get(table.lower(), set()):
            raise PermissionError(
                "Cette recherche nécessite des tables ou colonnes absentes de vos droits "
                "ou de la base. Demandez à l’administrateur de vérifier les accès.")


def _contexte(valeur):
    """Ne reprendre que des filtres structurés créés par ce module."""
    if not isinstance(valeur, dict) or valeur.get("version") != 1:
        return None
    lettres = valeur.get("lettres")
    if (not isinstance(lettres, list) or not lettres or len(lettres) > 7
            or any(x not in tuple("ABCDEFG") for x in lettres)):
        return None
    if valeur.get("cible") not in ("patrimoines", "logements", "occupants"):
        return None
    for cle, maximum in (("age_min", 130), ("etage_min", 99)):
        if cle in valeur and (type(valeur[cle]) is not int or not 0 <= valeur[cle] <= maximum):
            return None
    return {k: v for k, v in valeur.items()
            if k in ("version", "lettres", "cible", "age_min", "etage_min", "sans_ascenseur")}


def reconnaitre(question, schema, precedent=None):
    texte = normaliser(question)
    if re.fullmatch(r"j ai un controle ancols qui arrive peux tu m aider", texte):
        return Recherche(reponse=(
            "Oui. Je peux vous aider à retrouver et organiser les données disponibles "
            "pour préparer votre contrôle ANCOLS : clients, patrimoine, baux, impayés "
            "ou affaires. Par quelle liste ou quel indicateur souhaitez-vous commencer ?"))

    moraux = re.fullmatch(LISTE + r"(?P<cible>clients?|occupants?) (?:moraux|morales|personnes morales)", texte)
    if moraux:
        if moraux["cible"].startswith("client"):
            _exiger(schema, {"Client": ("ID_client", "Code_client", "Nom_prenom_client", "ID_client_lot"),
                              "Occupant": ("ID_client", "Type_personne")})
            return Recherche(sql='''SELECT c."ID_client", c."Code_client", c."Nom_prenom_client",
                COUNT(DISTINCT c."ID_client_lot") AS "Nombre_lots"
                FROM "Client" c
                WHERE EXISTS (SELECT 1 FROM "Occupant" o
                    WHERE o."ID_client" = c."ID_client" AND o."Type_personne" = 'Morale')
                GROUP BY c."ID_client", c."Code_client", c."Nom_prenom_client"
                ORDER BY c."Nom_prenom_client", c."ID_client"''',
                note="Clients rattachés à au moins un occupant de type 'Morale'.")
        _exiger(schema, {"Occupant": ("ID_occupant", "ID_client", "Type_personne", "Raison_sociale_occupant")})
        return Recherche(sql='''SELECT "ID_occupant", "ID_client", "Raison_sociale_occupant", "Type_personne"
            FROM "Occupant" WHERE "Type_personne" = 'Morale' ORDER BY "ID_occupant"''')

    dpe = re.fullmatch(LISTE + r"(?P<cible>patrimoines?|logements?|lots?) "
        r"(?:avec (?:un |une )?(?:lettre )?dpe(?: de dpe)?|dont (?:la )?(?:lettre )?dpe (?:est|vaut)) "
        r"(?P<lettres>[a-g](?: (?:ou|et) [a-g])*)", texte)
    if dpe:
        contexte = dict(version=1, lettres=sorted(set(re.findall(r"\b[a-g]\b", dpe["lettres"].upper(), re.I))),
                        cible="patrimoines" if dpe["cible"].startswith("patrimoine") else "logements")
        return _dpe(schema, contexte)

    age = re.fullmatch(LISTE + r"(?:personnes|occupants|gens) (?:de )?plus de (?P<age>\d{1,3}) ans "
                      r"qui (?:vivent|habitent|resident) dans ces logements", texte)
    etage = re.fullmatch(PARMI + DEMANDE + r"ceux qui habitent (?:au moins au|a partir du) "
                        r"(?P<etage>\d{1,2})\s*(?:eme|e|er)? etage sans ascenseur", texte)
    contact = re.fullmatch(PARMI + DEMANDE + r"(?:dans l ordre croissant )?le dernier contact"
                          r"(?: que l on a eu avec eux)?(?: dans l ordre croissant)?"
                          r"(?: je veux aussi pouvoir les contacter et les localiser)?", texte)
    if not (age or etage or contact):
        return None
    contexte = _contexte(precedent)
    if contexte is None or ((etage or contact) and contexte["cible"] != "occupants"):
        return Recherche(reponse="Commencez par rechercher les patrimoines ou logements avec un DPE F ou G, "
                         "puis les personnes concernées dans cette conversation, afin de conserver les mêmes critères.")
    if age:
        if int(age["age"]) > 130:
            return None
        contexte.update(cible="occupants", age_min=int(age["age"]))
    if etage:
        contexte.update(etage_min=int(etage["etage"]), sans_ascenseur=True)
    return _dpe(schema, contexte, contact=bool(contact))


def _dpe(schema, contexte, contact=False):
    requis = {"Lot": ("ID_lot", "ID_patrimoine"),
              "Patrimoine": ("ID_patrimoine", "Libelle_patrimoine", "Libelle_commune"),
              "Diagnostic": ("ID_diagnostic", "ID_lot"),
              "Diagnostic_valeur": ("ID_diagnostic", "Type_valeur", "Valeur")}
    # Les lettres sont exclusivement A..G, contrôlées à la reconnaissance/reprise.
    lettres = ", ".join("'" + x + "'" for x in contexte["lettres"])
    filtres = [f'''EXISTS (SELECT 1 FROM "Diagnostic" d
        JOIN "Diagnostic_valeur" dv ON dv."ID_diagnostic" = d."ID_diagnostic"
        WHERE d."ID_lot" = l."ID_lot" AND dv."Type_valeur" = 'Lettre_DPE_EP'
            AND dv."Valeur" IN ({lettres}))''']
    jointures = 'FROM "Lot" l JOIN "Patrimoine" p ON p."ID_patrimoine" = l."ID_patrimoine"'
    note = ""
    fin = ''
    if contexte["cible"] == "patrimoines":
        colonnes = 'p."ID_patrimoine", p."Libelle_patrimoine", p."Libelle_commune", COUNT(DISTINCT l."ID_lot") AS "Nombre_logements_DPE"'
        fin = 'GROUP BY p."ID_patrimoine", p."Libelle_patrimoine", p."Libelle_commune" ORDER BY p."Libelle_patrimoine"'
        note = "Ces patrimoines contiennent au moins un logement avec la lettre DPE demandée. Les relances portent sur ces logements."
    elif contexte["cible"] == "logements":
        colonnes = 'DISTINCT l."ID_lot", p."ID_patrimoine", p."Libelle_patrimoine", p."Libelle_commune"'
        fin = 'ORDER BY l."ID_lot"'
    else:
        requis.update({"Occupant": ("ID_occupant", "ID_client", "Nom_occupant", "Prenom_occupant", "Age_occupant"),
                        "Client_lot_pivot": ("ID_client", "ID_lot")})
        requis["Lot"] += ("Etage",)
        colonnes = '''DISTINCT o."ID_occupant", o."ID_client", o."Nom_occupant", o."Prenom_occupant",
            o."Age_occupant", l."ID_lot", l."Etage", p."ID_patrimoine", p."Libelle_patrimoine", p."Libelle_commune"'''
        jointures += ''' JOIN "Client_lot_pivot" cp ON cp."ID_lot" = l."ID_lot"
            JOIN "Occupant" o ON o."ID_client" = cp."ID_client"'''
        if "age_min" in contexte:
            filtres.append(f'o."Age_occupant" > {contexte["age_min"]}')
        if "etage_min" in contexte:
            filtres.append(f'l."Etage" >= {contexte["etage_min"]}')
        if contexte.get("sans_ascenseur"):
            requis.update({"Equipement": ("ID_patrimoine_lot", "Libelle_type_equipement", "Indicateur_activite"),
                            "Patrimoine_lot_pivot": ("ID_patrimoine_lot", "ID_lot")})
            filtres.append('''NOT EXISTS (SELECT 1 FROM "Equipement" e
                JOIN "Patrimoine_lot_pivot" pl ON pl."ID_patrimoine_lot" = e."ID_patrimoine_lot"
                WHERE pl."ID_lot" = l."ID_lot" AND e."Libelle_type_equipement" = 'Ascenseur'
                    AND e."Indicateur_activite" = 'Oui')''')
            note = "Logements sans ascenseur actif recensé dans les équipements rattachés au lot."
        fin = 'ORDER BY o."ID_occupant", l."ID_lot"'
        if contact:
            requis["Occupant"] += ("Telephone_occupant", "Mail_occupant")
            requis["Affaire"] = ("ID_client_demandeur_affaire", "Date_ouverture")
            colonnes += ', o."Telephone_occupant", o."Mail_occupant", a."Derniere_ouverture_affaire"'
            jointures += ''' LEFT JOIN (
                SELECT "ID_client_demandeur_affaire", MAX(date("Date_ouverture")) AS "Derniere_ouverture_affaire"
                FROM "Affaire" WHERE date("Date_ouverture") < '2090-01-01'
                GROUP BY "ID_client_demandeur_affaire"
            ) a ON a."ID_client_demandeur_affaire" = o."ID_client"'''
            fin = 'ORDER BY a."Derniere_ouverture_affaire" IS NULL, a."Derniere_ouverture_affaire", o."ID_occupant", l."ID_lot"'
            note += (" Tri croissant sur la dernière ouverture d’affaire du client, utilisée comme repère de contact ; "
                     "les dates non renseignées sont placées à la fin. La localisation correspond à la résidence.")
    _exiger(schema, requis)
    return Recherche(sql="SELECT " + colonnes + " " + jointures + " WHERE " + " AND ".join(filtres) + " " + fin,
                     contexte=contexte, note=note.strip())
