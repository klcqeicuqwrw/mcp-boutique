import asyncio
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

# ---------------------------------------------------------------------------
# Compatibilité SDK MCP (Model Context Protocol)
# Le protocole MCP permet à des IA de se connecter à des outils externes.
# Ce bloc gère les différentes versions de la librairie 'mcp' de Python.
# ---------------------------------------------------------------------------
try:
    # Tentative d'import pour le SDK MCP version 1.x
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError as exc:
    # Si le paquet global n'est pas du tout installé, on avertit l'utilisateur
    if exc.name == "mcp":
        raise ModuleNotFoundError(
            "Le paquet 'mcp' n'est pas installé dans cet environnement Python. "
            "Installez-le avec : pip install mcp"
        ) from exc

    # Si on arrive ici, c'est que le SDK est en version 2.x : FastMCP a été 
    # renommé en MCPServer et a changé de dossier. On gère l'adaptation.
    from mcp.server.mcpserver import MCPServer

    class FastMCP(MCPServer):
        """Wrapper de compatibilité pour faire fonctionner l'ancien code avec l'API serveur MCP v2."""

        def run_stdio(self) -> None:
            # Exécute la boucle asynchrone pour la communication standard (stdio)
            asyncio.run(self.run_stdio_async())

# Initialisation du serveur MCP avec un nom identifiable par l'IA
mcp = FastMCP("BailleurSocialDatabase")

# ---------------------------------------------------------------------------
# Configuration de la base de données
# Ce fichier expose les fonctions SQLite utiles à un client MCP (l'IA).
# L'idée est simple : un agent externe (ex: Claude Desktop) peut demander 
# le schéma de la base et exécuter uniquement des requêtes de lecture, jamais des mises à jour.
# ---------------------------------------------------------------------------

# Limite le nombre de résultats pour éviter de saturer la mémoire de l'IA (et ses tokens)
MAX_ROWS = 500

# Chemin vers le fichier SQLite. Par défaut "bailleur_social.db" dans le même dossier
DATABASE_PATH = Path(
    os.environ.get("SQLITE_DB_PATH", "bailleur_social.db")
).expanduser().resolve()


def _connect_read_only() -> sqlite3.Connection:
    """Ouvre la base SQLite configurée strictement en lecture seule."""
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"Base SQLite introuvable: {DATABASE_PATH}. "
            "Définissez SQLITE_DB_PATH ou créez bailleur_social.db."
        )

    # Le paramètre ?mode=ro (read-only) est une sécurité physique empêchant
    # toute altération de la base (INSERT, UPDATE, DELETE).
    connection = sqlite3.connect(
        f"{DATABASE_PATH.as_uri()}?mode=ro",
        uri=True,
    )
    # Permet d'accéder aux colonnes par leur nom plutôt que par un index numérique
    connection.row_factory = sqlite3.Row
    return connection


def _remove_leading_comments(query: str) -> str:
    """
    Retire les commentaires SQL au début de la requête.
    Cette étape est cruciale car l'IA ajoute parfois des commentaires,
    ce qui empêcherait notre regex (plus bas) de détecter si le premier
    mot est bien un 'SELECT'.
    """
    remaining = query.lstrip()
    while remaining.startswith("--") or remaining.startswith("/*"):
        # Supprime les commentaires sur une seule ligne (--)
        if remaining.startswith("--"):
            end = remaining.find("\n")
            if end == -1:
                return ""
            remaining = remaining[end + 1 :].lstrip()
            continue

        # Supprime les blocs de commentaires multilignes (/* ... */)
        end = remaining.find("*/", 2)
        if end == -1:
            return ""
        remaining = remaining[end + 2 :].lstrip()
    return remaining


def _validate_read_query(query: str) -> str:
    """
    Validation de sécurité de la requête générée par l'IA.
    Vérifie qu'il s'agit bien d'une lecture simple et bloque les requêtes multiples.
    """
    query = _remove_leading_comments(query.strip())
    
    if not query:
        raise ValueError("La requête SQL ne peut pas être vide.")
        
    # Interdit le point-virgule au milieu de la requête pour empêcher l'injection 
    # de multiples commandes (ex: SELECT * FROM X ; DROP TABLE Y)
    if ";" in query.rstrip(";"):
        raise ValueError("Une seule requête SQL est autorisée.")
        
    # N'autorise que les mots clés de lecture (SELECT, WITH) ou d'analyse (EXPLAIN)
    if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", query, re.IGNORECASE):
        raise ValueError("Vous n'êtes pas autorisé à exécuter cette requête.")
        
    return query.rstrip(";").strip()


# ---------------------------------------------------------------------------
# Outils exposés à l'IA (Tools)
# Le décorateur @mcp.tool() permet à l'IA de voir et d'utiliser ces fonctions.
# ---------------------------------------------------------------------------

@mcp.tool()
def dire_bonjour(nom: str) -> str:
    """Renvoie un message de salutation personnalisé. 
    (Outil de test simple pour vérifier que le serveur MCP communique bien)."""
    return f"Bonjour, {nom} !"


@mcp.tool()
def obtenir_schema() -> str:
    """Retourne les tables, colonnes et index disponibles dans la base SQLite.
    
    C'est le premier outil que l'IA va appeler. Le client MCP demande d'abord 
    le schéma pour savoir quelles tables existent et quelles colonnes sont 
    disponibles avant d'inventer une requête SQL.
    """
    with closing(_connect_read_only()) as connection:
        objects = connection.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE type IN ('table', 'view', 'index')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        ).fetchall()

    # Convertit la réponse SQL en JSON compréhensible par l'IA
    return json.dumps(
        [dict(row) for row in objects],
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def executer_requete_sql(requete: str) -> str:
    """Exécute une requête SQL de lecture et retourne les résultats en JSON.

    L'IA utilise cet outil APRÈS avoir consulté 'obtenir_schema'. 
    Elle traduit la demande de l'utilisateur (en langage naturel) en une 
    requête SQL précise, l'envoie ici, et récupère les données brutes.
    """
    # 1. On valide et sécurise la requête
    safe_query = _validate_read_query(requete)

    try:
        # 2. Exécution sur la base de données
        with closing(_connect_read_only()) as connection:
            cursor = connection.execute(safe_query)
            # Récupère le nom des colonnes pour formater le résultat
            columns = [description[0] for description in cursor.description or []]
            # Limite l'extraction à MAX_ROWS + 1 pour savoir si on a dépassé la limite
            rows = cursor.fetchmany(MAX_ROWS + 1)
    except sqlite3.Error as error:
        raise RuntimeError(f"Erreur SQLite pendant l'exécution: {error}") from error

    # 3. Tronque les résultats s'il y a trop de données
    truncated = len(rows) > MAX_ROWS
    if truncated:
        rows = rows[:MAX_ROWS]

    # 4. Formate et renvoie le JSON à l'IA
    return json.dumps(
        {
            "columns": columns,
            "rows": [dict(zip(columns, row)) for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
            "max_rows": MAX_ROWS,
        },
        ensure_ascii=False,
        default=str,
        indent=2,
    )


# ---------------------------------------------------------------------------
# Point d'entrée du serveur
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Le serveur MCP peut communiquer de deux manières :
    # - stdio (standard in/out) : L'IA et ce script tournent sur la même machine. L'IA lance le script et lui "parle" via le terminal.
    # - http : Le serveur écoute sur un port réseau, utile si l'IA est distante.
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "http":
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        try:
            mcp.run(transport="streamable-http", host=host, port=port)
        except AttributeError:
            # Fallback en cas de problème avec le transport HTTP
            mcp.run_stdio()
    else:
        try:
            # Lancement par défaut
            mcp.run()
        except AttributeError:
            # Lancement via l'entrée/sortie standard (stdio)
            mcp.run_stdio()