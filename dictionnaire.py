"""Lecture commune des dictionnaires Markdown, anciens tableaux et fiches DWH."""
import re
import unicodedata
from pathlib import Path


def lire_dictionnaire(path: Path) -> dict:
    if not path.is_file():
        return {}
    texte = path.read_text(encoding="utf-8")
    sections = list(re.finditer(r"^(#{2,3}) ([\w]+)[ \t]*$", texte, re.M))
    resultat = {}
    fin_table = -1
    for i, section in enumerate(sections):
        if section.start() < fin_table:
            continue  # Sous-titre d'une fiche, par exemple « ### Identification ».
        fin = next((s.start() for s in sections[i + 1:] if len(s[1]) <= len(section[1])), len(texte))
        bloc = texte[section.end():fin]
        entree = dict(nom=section[2], theme="", description="", jointures="", colonnes=[], rgpd=set())
        colonne = None
        for ligne in bloc.splitlines():
            ligne = ligne.strip()
            if ligne.startswith("|"):
                cellules = [x.strip().strip("`") for x in ligne.strip("|").split("|")]
                if len(cellules) >= 4 and cellules[0].lower() != "colonne" and not cellules[0].startswith("-"):
                    colonne = dict(nom=cellules[0], type=cellules[1], cles=cellules[2], description=cellules[3])
                    entree["colonnes"].append(colonne)
            else:
                debut = re.match(r"^- (.+?) — Type SQLite : ([^.]+)\.", ligne)
                if debut:
                    colonne = dict(nom=debut[1], type=debut[2], cles="", description="")
                    entree["colonnes"].append(colonne)
                elif colonne and ligne.startswith("Confidentialité :") and "RGPD" in ligne:
                    colonne["cles"] = "RGPD"
                elif colonne and ligne.startswith("Description :"):
                    colonne["description"] = ligne.removeprefix("Description :").strip()
                elif colonne and ligne.startswith("Valeurs observées"):
                    # Vocabulaire utile au SQL, plafonné pour ne pas reproduire toute la base.
                    colonne["valeurs"] = ligne[:600]
                elif ligne.startswith("*"):
                    entree["theme"] = ligne.strip("*").split("·")[0].strip()
                elif ligne.startswith("Jointures"):
                    entree["jointures"] = ligne
                elif ligne and not ligne.startswith(("#", "|", "-")) and not entree["description"]:
                    entree["description"] = ligne
        # Les titres de guide et annexes ne sont pas des tables.
        if entree["colonnes"]:
            entree["rgpd"] = {c["nom"].lower() for c in entree["colonnes"] if "RGPD" in c["cles"].upper()}
            resultat[section[2].lower()] = entree
            fin_table = fin
    return resultat


REGLES_SQL = """Utiliser exclusivement le schéma autorisé fourni. SQLite : citer les
identifiants avec des guillemets doubles. Les dates sont du texte ISO : filtrer
par intervalle ou substr. Les dates 2099-12-31 et 2099-01-01 sont des sentinelles.
Conserver les zéros initiaux des codes texte. Vérifier les valeurs catégorielles.
Une jointure peut multiplier les lignes : compter les entités avec COUNT(DISTINCT
identifiant) et agréger au bon grain avant de joindre les historiques mensuels.
Ne pas inventer de résultat ni généraliser un échantillon. Préférer les agrégats
pour les questions de total ; limiter les listes détaillées."""


def _mots(texte):
    texte = "".join(c for c in unicodedata.normalize("NFKD", texte.lower())
                    if not unicodedata.combining(c)).replace("_", " ")
    mots = set(re.findall(r"[a-z0-9]{3,}", texte))
    # Les demandes sont souvent au pluriel, les noms du schéma au singulier.
    return {"moral" if m in {"moraux", "morale", "morales"}
            else m[:-1] if m.endswith("s") and len(m) > 3 else m for m in mots}


def contexte_dictionnaire(path: Path, schema: dict, question: str, limite=18000) -> str:
    """Filtre tables ET colonnes avant de classer les définitions pertinentes.

    Les descriptions libres, exemples, guides et jointures non filtrés ne sont
    jamais copiés : ils peuvent mentionner des données interdites.
    """
    mots = _mots(question)
    candidats = []
    dico = lire_dictionnaire(path)
    interdits = {e['nom'] for t, e in dico.items() if t not in schema}
    interdits.update(c['nom'] for t, e in dico.items() for c in e['colonnes']
                     if t in schema and c['nom'].lower() not in schema[t])
    for table, entree in dico.items():
        autorisees = schema.get(table)
        if autorisees is None:
            continue
        for col in entree["colonnes"]:
            if col["nom"].lower() not in autorisees:
                continue
            texte = f"{entree['nom']}.{col['nom']} ({col['type']}) : {col['description']}"
            # Ne pas transmettre de valeurs personnelles, même si la consultation est autorisée.
            if col["nom"].lower() not in entree["rgpd"] and col.get("valeurs"):
                texte += " ; " + col["valeurs"]
            # Écarte les descriptions contenant des identifiants documentés interdits.
            interdit = any(
                re.search(r"(?<!\w)" + re.escape(nom) + r"(?!\w)", texte, re.I)
                for nom in interdits
            )
            if interdit:
                continue
            # Les noms de tables et colonnes priment sur un mot dans une longue
            # liste de valeurs. Les mêmes mots servent aux deux côtés du score.
            score = (4 * len(mots & _mots(entree['nom'] + " " + col['nom']))
                     + 2 * len(mots & _mots(col['description']))
                     + len(mots & _mots(texte)))
            candidats.append((score, texte))
    relations = contexte_relations(path, schema, dico)
    base = REGLES_SQL[:limite]
    for relation in relations.splitlines():
        if len(base) + len(relation) + 1 <= min(limite, 6000):
            base += "\n" + relation
    morceaux, taille = [base], len(base)
    for _, texte in sorted(candidats, key=lambda x: -x[0]):
        if taille + len(texte) + 1 > limite:
            continue
        morceaux.append(texte)
        taille += len(texte) + 1
    return "\n".join(morceaux)


def contexte_relations(path: Path, schema: dict, dico: dict) -> str:
    """Extrait les grains et jointures du guide DWH sans recopier les lignes libres."""
    if not path.is_file():
        return ""
    lignes = []
    rubrique = ""
    for ligne in path.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("### "):
            rubrique = "grain" if "Grain des tables" in ligne else "jointures" if "Jointures validées" in ligne else ""
        if not rubrique or not ligne.startswith("|"):
            continue
        cellules = [x.strip() for x in ligne.strip("|").split("|")]
        if rubrique == "grain" and len(cellules) == 3:
            tables = re.findall(r"\w+", cellules[0].lower())
            for t in tables:
                if t not in schema or t not in dico:
                    continue
                cle = [x for x in re.findall(r"\w+", cellules[2]) if x.lower() in schema[t]]
                if cle:
                    lignes.append(f"Grain {dico[t]['nom']} : clés {', '.join(cle)}. Vérifier les doublons avant toute jointure.")
        if rubrique == "jointures" and len(cellules) == 4:
            sources = [x.lower() for x in re.findall(r"\w+", cellules[0]) if x.lower() in schema and x.lower() in dico]
            cibles = [x.lower() for x in re.findall(r"\w+", cellules[1]) if x.lower() in schema and x.lower() in dico]
            termes = re.findall(r"\w+", cellules[2])
            egalite = re.search(r"(\w+)\s*=\s*(\w+)", cellules[2])
            for source in sources:
                for cible in cibles:
                    paires = [(egalite[1], egalite[2])] if egalite else [(x, x) for x in termes]
                    for a, b in paires:
                        if a.lower() in schema[source] and b.lower() in schema[cible]:
                            lignes.append(f"Jointure validée : {dico[source]['nom']}.{a} = {dico[cible]['nom']}.{b}")
    return "\n".join(dict.fromkeys(lignes))
