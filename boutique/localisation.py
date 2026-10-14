"""Reconnaissance des demandes de carte et identifiants utilisables."""
import re
import unicodedata


def normaliser(texte):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(
        c for c in unicodedata.normalize("NFKD", texte.lower()) if not unicodedata.combining(c))).split())


def demandee(question):
    texte = normaliser(question)
    if re.search(r"\b(sans|pas de|pas sur) (?:la |une )?carte\b|\bne\b.*\bpas\b.*\blocalis|\bne\b.*\blocalis\w*\b.*\bpas\b", texte):
        return False
    return bool(re.search(r"\b(?:localis\w*|geolocalis\w*|cartograph\w*)\b|\bsur (?:la|une) carte\b|\bou se (?:trouve|trouvent|situe|situent)\b", texte))


def reprise(question):
    return normaliser(question) in {
        "localise ces resultats", "localiser ces resultats", "localise les resultats",
        "localise cette selection", "localise ces logements", "localise ces personnes",
        "localise ces clients", "affiche ces resultats sur une carte",
        "montre ces resultats sur la carte", "ou se trouvent ces resultats",
    }


IDENTIFIANTS = ("id_patrimoine", "id_lot", "id_client", "id_occupant")


def possible(resultat):
    return any(row.get(c) for c in resultat["columns"] if c.lower() in IDENTIFIANTS for row in resultat["rows"])
