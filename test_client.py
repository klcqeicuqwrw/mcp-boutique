"""
Faux assistant IA pour tester server.py sans ouvrir VS Code.

Lance le serveur, liste les outils, exécute une série de vérifications
(dont des requêtes qui DOIVENT être refusées), puis ouvre un mode interactif.

Usage :  python test_client.py
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def appeler(session, outil: str, arguments: dict) -> str:
    """Appelle un outil et renvoie le texte de la réponse (ou l'erreur)."""
    resultat = await session.call_tool(outil, arguments)
    texte = resultat.content[0].text if resultat.content else ""
    # Le nom de l'attribut diffère selon la version du SDK (2.x : is_error, 1.x : isError)
    en_erreur = getattr(resultat, "is_error", getattr(resultat, "isError", False))
    return ("[ERREUR] " if en_erreur else "") + texte


def afficher(titre: str, texte: str, max_car: int = 700) -> None:
    print(f"\n--- {titre} ---")
    print(texte if len(texte) <= max_car else texte[:max_car] + f" ... (+{len(texte) - max_car} car.)")


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,  # même interpréteur Python que ce script
        args=["server.py"],
        env=os.environ.copy(),
    )
    async with stdio_client(params) as (lecture, ecriture):
        async with ClientSession(lecture, ecriture) as session:
            await session.initialize()

            outils = await session.list_tools()
            print("Outils disponibles :")
            for outil in outils.tools:
                resume = (outil.description or "").strip().splitlines()[0]
                print(f"  - {outil.name} : {resume}")

            # 1. Exploration
            texte = await appeler(session, "lister_tables", {})
            afficher("lister_tables", texte, 500)
            tables = json.loads(texte)["tables"]
            premiere = tables[0]["table"]

            afficher("rechercher_colonnes('date')", await appeler(session, "rechercher_colonnes", {"mot_cle": "date", "limite": 3}))
            afficher(f"decrire_table({premiere})", await appeler(session, "decrire_table", {"table": premiere}), 600)
            afficher(f"apercu_table({premiere})", await appeler(session, "apercu_table", {"table": premiere, "limite": 2}), 400)

            # 2. Requête normale
            afficher("SELECT valide", await appeler(session, "executer_requete_sql",
                     {"requete": f'SELECT COUNT(*) AS nb FROM "{premiere}"'}))

            # 3. Requêtes qui DOIVENT être refusées
            interdites = {
                "écriture": f'DELETE FROM "{premiere}"',
                "plusieurs requêtes": f'SELECT 1; DROP TABLE "{premiere}"',
                "tables internes": "SELECT * FROM sqlite_master",
                "PRAGMA": "PRAGMA table_info('x')",
            }
            print("\n=== Requêtes qui doivent être refusées ===")
            for nom, sql in interdites.items():
                reponse = await appeler(session, "executer_requete_sql", {"requete": sql})
                statut = "OK (refusée)" if reponse.startswith("[ERREUR]") else "PROBLÈME (acceptée !)"
                print(f"  {nom:<20} -> {statut}")

            # 4. Mode interactif
            print("\n--- Mode interactif ---")
            print("Tape une requête SQL, ou 'quit' pour sortir.")
            while True:
                try:
                    requete = input("\nSQL> ").strip()
                except EOFError:
                    break
                if requete.lower() in ("quit", "exit", ""):
                    break
                print(await appeler(session, "executer_requete_sql", {"requete": requete}))


if __name__ == "__main__":
    asyncio.run(main())