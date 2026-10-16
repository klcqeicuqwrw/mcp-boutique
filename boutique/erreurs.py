"""Messages publics : diagnostiquer sans exposer les réponses brutes ni les clés."""
import httpx


def erreur_ia(exc, fournisseur, etape="generation"):
    nom = {"openai": "OpenAI", "groq": "Groq", "gemini": "Gemini"}.get(fournisseur, fournisseur)
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    # Le texte ne sert qu'à classer l'erreur ; il n'est jamais renvoyé au navigateur.
    texte = (str(exc) + " " + str(getattr(exc, "body", ""))).lower()
    genre = type(exc).__name__.lower()
    if etape == "sql":
        if "trop longue" in texte or "interrupted" in texte:
            return "La recherche dépasse le temps autorisé. Précisez une commune, une période ou un type de dossier pour réduire les données à traiter."
        return "La requête produite par l’IA ne peut pas être exécutée dans la base. Reformulez la question avec les données et les filtres souhaités. Si cela se reproduit, créez un ticket."
    if "api_key" in texte and ("manquante" in texte or "not configured" in texte):
        return f"{nom} n’est pas configuré : sa clé API est absente sur le serveur. Demandez à l’administrateur de configurer ce fournisseur ou choisissez l’autre modèle."
    if status == 413 or "contextegroqtroplong" in genre or "request too large" in texte:
        return f"La demande dépasse la taille de contexte autorisée par {nom}. Raccourcissez la question ou choisissez l’autre fournisseur. Si cela persiste, faites vérifier les limites du compte API."
    if any(x in texte for x in ("credit_balance_exhausted", "insufficient_quota", "billing_hard_limit", "billing_not_active")):
        return f"{nom} refuse la demande : le crédit API est épuisé ou la facturation API n’est pas active. L’administrateur doit vérifier le compte API. Choisissez l’autre modèle en attendant."
    if status == 401 or any(x in texte for x in ("api_key_invalid", "invalid_api_key", "api key not valid")):
        return f"{nom} refuse la clé API : elle est invalide, expirée ou révoquée. Demandez à l’administrateur de vérifier la clé du serveur."
    if status == 403:
        return f"{nom} refuse l’accès : le compte API n’a pas l’autorisation nécessaire pour ce service ou ce modèle. Contactez l’administrateur."
    if status == 404 or "model_not_found" in texte:
        return f"Le modèle configuré pour {nom} est introuvable ou inaccessible à ce compte. L’administrateur doit vérifier le nom du modèle et son accès."
    if status == 429 or "resource_exhausted" in texte:
        return f"{nom} a atteint une limite de requêtes ou de quota API. Réessayez dans quelques instants ou choisissez l’autre modèle. Si le blocage persiste, faites vérifier le quota du compte."
    if status == 504 or "timeout" in genre or "deadline_exceeded" in texte or isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        return f"{nom} n’a pas répondu dans le délai autorisé. Réessayez avec une question plus courte ou choisissez l’autre modèle."
    if isinstance(exc, (ConnectionError, httpx.NetworkError)) or "connection" in genre:
        return f"Le serveur de l’application ne parvient pas à joindre {nom}. La connexion réseau ou l’accès au fournisseur est interrompu. Réessayez puis contactez l’assistance si cela persiste."
    if isinstance(status, int) and status >= 500:
        return f"Le service {nom} rencontre une panne temporaire. Réessayez plus tard ou choisissez l’autre modèle."
    if isinstance(exc, ValueError):
        return f"{nom} a renvoyé une réponse inexploitable pour cette demande. Reformulez votre question ; si le problème se répète, créez un ticket."
    if status == 400:
        return f"{nom} a rejeté la demande envoyée par l’application. Essayez une question plus courte. Si cela persiste, l’assistance doit vérifier la configuration du modèle."
    return f"Un incident inattendu s’est produit pendant l’appel à {nom}. Sa cause n’a pas pu être identifiée. Réessayez puis créez un ticket si l’incident persiste."
