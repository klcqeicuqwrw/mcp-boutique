"""Évaluation facultative du modèle sur des questions métier à résultat connu.

Lancer explicitement : python eval_gemini.py. Consomme des appels Gemini.
Utilise exclusivement la base configurée, en lecture seule, sans base applicative.
"""
import json
import sys

import config
import securite as S
from api import DICTIONNAIRE_PATH, generer_sql
from dictionnaire import contexte_dictionnaire

REFERENCES = [
    ("Combien de clients distincts y a-t-il, en comptant un client une seule fois même s'il a plusieurs lots ?",
     "SELECT COUNT(DISTINCT ID_client) FROM Client"),
    ("Combien de lots sont enregistrés ?", "SELECT COUNT(DISTINCT ID_lot) FROM Lot"),
    ("Quel est le montant total TTC des commandes ?", "SELECT SUM(Montant_TTC) FROM Commande"),
    ("Combien de diagnostics sont marqués périmés (Oui) ?",
     "SELECT COUNT(*) FROM Diagnostic WHERE Indicateur_diagnostic_perime='Oui'"),
]


def scalaire(resultat):
    if len(resultat["rows"]) != 1 or len(resultat["columns"]) != 1:
        raise ValueError("La réponse doit être un seul agrégat.")
    return next(iter(resultat["rows"][0].values()))


def main():
    user = {"role": "admin", "service_id": None}
    schema = S.schema_text(None)
    autorise = {t.lower(): {c.lower() for c in cols} for t, cols in S.tables_info().items()}
    echecs = 0
    for question, reference in REFERENCES:
        attendu = scalaire(S.run_query(user, reference))
        sql, obtenu, erreur = None, None, None
        try:
            sql = generer_sql(question, schema, [], dictionnaire=contexte_dictionnaire(DICTIONNAIRE_PATH, autorise, question))
            obtenu = scalaire(S.run_query(user, sql))
            ok = abs(obtenu - attendu) < 0.000001 if isinstance(attendu, (int, float)) and isinstance(obtenu, (int, float)) else obtenu == attendu
        except Exception as exc:
            ok, erreur = False, str(exc)
        echecs += not ok
        print(json.dumps(dict(question=question, sql=sql, attendu=attendu, obtenu=obtenu, ok=ok, erreur=erreur), ensure_ascii=False))
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
