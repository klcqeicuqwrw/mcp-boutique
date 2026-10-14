
TYPES_GRAPH = ("bar", "line", "pie", "doughnut")

def choisir_graphique(question, res):
    """
    Choisit le type de graphique et les colonnes à utiliser.
    Déduit le graphique du tableau et de la demande sans appel à Gemini.
    """
    cols, rows = res["columns"], res["rows"]
    
    # Identifie quelles colonnes du résultat SQL contiennent uniquement des nombres
    est_num = lambda c: any(isinstance(r.get(c), (int, float)) for r in rows) and \
        all(r.get(c) is None or isinstance(r.get(c), (int, float)) for r in rows)
    nums = [c for c in cols if est_num(c)]
    
    # S'il n'y a pas assez de données pour faire un graphique, on annule
    if len(cols) < 2 or not rows or not nums:
        return None
        
    # Le type et les axes se déduisent du tableau, sans appel réseau.
    x = next((c for c in cols if c not in nums), cols[0])
    y = [c for c in nums if c != x][:1]
    if not y:
        return None
    q = question.lower()
    type_ = "bar"
    if any(mot in q for mot in ("camembert", "pie", "circulaire")) and len(rows) <= 8:
        type_ = "pie"
    elif "doughnut" in q and len(rows) <= 8:
        type_ = "doughnut"
    elif any(mot in q for mot in ("courbe", "evolution", "évolution", "line")):
        type_ = "line"
    spec = {"type": type_, "x": x, "y": y, "titre": question[:100]}

    # Les camemberts/doughnuts n'ont besoin que d'une seule série de données (un seul Y)
    if spec["type"] in ("pie", "doughnut"):
        spec["y"] = spec["y"][:1]
    spec["titre"] = str(spec.get("titre") or "")[:100] # Sécurité sur la longueur du titre
    return spec

