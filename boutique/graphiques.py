import json
from google.genai import types
from api import _appeler_gemini_avec_retry

TYPES_GRAPH = ("bar", "line", "pie", "doughnut")

def choisir_graphique(question, res):
    """
    Choisit le type de graphique et les colonnes à utiliser.
    En cas d'échec de l'IA, utilise une méthode de secours (repli heuristique).
    """
    cols, rows = res["columns"], res["rows"]
    
    # Identifie quelles colonnes du résultat SQL contiennent uniquement des nombres
    est_num = lambda c: any(isinstance(r.get(c), (int, float)) for r in rows) and \
        all(r.get(c) is None or isinstance(r.get(c), (int, float)) for r in rows)
    nums = [c for c in cols if est_num(c)]
    
    # S'il n'y a pas assez de données pour faire un graphique, on annule
    if len(cols) < 2 or not rows or not nums:
        return None
        
    spec = None
    try:
        # On demande à Gemini d'analyser les données pour recommander le meilleur graphique
        r = _appeler_gemini_avec_retry(
            f"Question : {question}\nColonnes : {cols} (numériques : {nums})\n"
            f"Début des lignes : {json.dumps(rows[:3], ensure_ascii=False, default=str)}\n"
            f"Nombre de lignes : {len(rows)}\n"
            'Choisis le graphique le plus parlant. Réponds en JSON : {"type":"bar|line|pie|doughnut",'
            '"x":"colonne","y":["colonnes numériques"],"titre":"titre court"}. '
            "line = évolution dans le temps ; pie/doughnut = parts d'un tout (8 lignes max, un seul y) ; sinon bar.",
            types.GenerateContentConfig(temperature=0, response_mime_type="application/json"))
        spec = json.loads(r.text)
    except Exception:
        spec = None
        
    # Vérifie si le JSON renvoyé par l'IA est valide et correspond à nos colonnes
    ok = isinstance(spec, dict) and spec.get("type") in TYPES_GRAPH and spec.get("x") in cols \
        and isinstance(spec.get("y"), list) and spec["y"] and all(y in nums for y in spec["y"])
        
    # Si l'IA a échoué ou répondu n'importe quoi, on crée un graphique "Barres" par défaut
    if not ok:
        x = next((c for c in cols if c not in nums), cols[0]) # On prend la 1ère colonne texte pour l'axe X
        y = [c for c in nums if c != x][:1] # On prend la 1ère colonne numérique pour l'axe Y
        if not y:
            return None
        spec = {"type": "bar", "x": x, "y": y, "titre": question[:60]}
        
    # Les camemberts/doughnuts n'ont besoin que d'une seule série de données (un seul Y)
    if spec["type"] in ("pie", "doughnut"):
        spec["y"] = spec["y"][:1]
    spec["titre"] = str(spec.get("titre") or "")[:100] # Sécurité sur la longueur du titre
    return spec

