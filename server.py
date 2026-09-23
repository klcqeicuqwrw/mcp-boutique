import asyncio
import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

try:
    # SDK MCP v1.x
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError as exc:
    if exc.name == "mcp":
        raise ModuleNotFoundError(
            "Le paquet 'mcp' n'est pas installé dans cet environnement Python. "
            "Installez-le avec : pip install mcp"
        ) from exc

    # SDK MCP v2.x : FastMCP a été renommé MCPServer et déplacé
    from mcp.server.mcpserver import MCPServer

    class FastMCP(MCPServer):
        """Wrapper de compatibilité pour l'API serveur MCP v2."""

        def run_stdio(self) -> None:
            asyncio.run(self.run_stdio_async())

mcp = FastMCP("BoutiqueDatabase")

MAX_ROWS = 500
DATABASE_PATH = Path(
    os.environ.get("SQLITE_DB_PATH", "boutique.db")
).expanduser().resolve()


def _connect_read_only() -> sqlite3.Connection:
    """Ouvre la base SQLite configurée en lecture seule."""
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"Base SQLite introuvable: {DATABASE_PATH}. "
            "Définissez SQLITE_DB_PATH ou créez boutique.db."
        )

    connection = sqlite3.connect(
        f"{DATABASE_PATH.as_uri()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    return connection


def _remove_leading_comments(query: str) -> str:
    """Retire les commentaires SQL avant de vérifier le mot-clé de la requête."""
    remaining = query.lstrip()
    while remaining.startswith("--") or remaining.startswith("/*"):
        if remaining.startswith("--"):
            end = remaining.find("\n")
            if end == -1:
                return ""
            remaining = remaining[end + 1 :].lstrip()
            continue

        end = remaining.find("*/", 2)
        if end == -1:
            return ""
        remaining = remaining[end + 2 :].lstrip()
    return remaining


def _validate_read_query(query: str) -> str:
    query = _remove_leading_comments(query.strip())
    if not query:
        raise ValueError("La requête SQL ne peut pas être vide.")
    if ";" in query.rstrip(";"):
        raise ValueError("Une seule requête SQL est autorisée.")
    if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", query, re.IGNORECASE):
        raise ValueError("Seules les requêtes SELECT, WITH et EXPLAIN sont autorisées.")
    return query.rstrip(";").strip()


@mcp.tool()
def dire_bonjour(nom: str) -> str:
    """Renvoie un message de salutation personnalisé."""
    return f"Bonjour, {nom} !"


@mcp.tool()
def obtenir_schema() -> str:
    """Retourne les tables, colonnes et index disponibles dans la base SQLite."""
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

    return json.dumps(
        [dict(row) for row in objects],
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def executer_requete_sql(requete: str) -> str:
    """Exécute une requête SQL de lecture et retourne les résultats en JSON.

    Utilisez cet outil après avoir consulté obtenir_schema. Copilot peut
    traduire une demande en langage naturel en requête SQL adaptée au schéma.
    """
    safe_query = _validate_read_query(requete)

    try:
        with closing(_connect_read_only()) as connection:
            cursor = connection.execute(safe_query)
            columns = [description[0] for description in cursor.description or []]
            rows = cursor.fetchmany(MAX_ROWS + 1)
    except sqlite3.Error as error:
        raise RuntimeError(f"Erreur SQLite pendant l'exécution: {error}") from error

    truncated = len(rows) > MAX_ROWS
    if truncated:
        rows = rows[:MAX_ROWS]

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


if __name__ == "__main__":
    # MCP_TRANSPORT=stdio (par défaut, pour Claude Desktop en local)
    # MCP_TRANSPORT=http  (pour une exposition réseau, ex: Copilot Studio)
    transport = os.environ.get("MCP_TRANSPORT", "stdio")

    if transport == "http":
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        try:
            mcp.run(transport="streamable-http", host=host, port=port)
        except AttributeError:
            mcp.run_stdio()
    else:
        try:
            mcp.run()
        except AttributeError:
            mcp.run_stdio()