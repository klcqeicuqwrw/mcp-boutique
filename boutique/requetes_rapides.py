"""Comptages sans IA pour des questions autonomes strictement reconnues."""
import re
import unicodedata

ENTITES = {
    "clients": ("Client", "ID_client"), "lots": ("Lot", "ID_lot"),
    "patrimoines": ("Patrimoine", "ID_patrimoine"), "commandes": ("Commande", "ID_commande"),
    "occupants": ("Occupant", "ID_occupant"), "baux": ("Bail", "ID_bail"),
    "diagnostics": ("Diagnostic", "ID_diagnostic"),
}


def sql_comptage(question, schema):
    texte = "".join(c for c in unicodedata.normalize("NFKD", question.lower()) if not unicodedata.combining(c))
    texte = re.sub(r"[?.,!]+$", "", texte.strip()).strip()
    correspondance = re.fullmatch(
        r"(?:combien de|quel est le nombre(?: total)? de|nombre(?: total)? de) "
        r"(clients|lots|patrimoines|commandes|occupants|baux|diagnostics)"
        r"(?: distincts)?(?: (?:y a-t-il|avons-nous|sont enregistres|au total))?", texte)
    if not correspondance:
        return None
    table, cle = ENTITES[correspondance[1]]
    # Les permissions restent appliquées à l'exécution ; ne proposer que le schéma autorisé.
    if cle.lower() not in schema.get(table.lower(), set()):
        return None
    return f'SELECT COUNT(DISTINCT "{cle}") AS nombre FROM "{table}"'
