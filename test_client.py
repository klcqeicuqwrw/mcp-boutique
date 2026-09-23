import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,  # utilise le même interpréteur Python que celui-ci
        args=["server.py"],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("\nOutils disponibles :")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            print("\n--- Test: dire_bonjour ---")
            result = await session.call_tool("dire_bonjour", {"nom": "Romain"})
            print(result.content[0].text)

            print("\n--- Test: obtenir_schema ---")
            result = await session.call_tool("obtenir_schema", {})
            print(result.content[0].text)

            # Boucle interactive pour tester tes propres requêtes SQL
            print("\n--- Mode interactif (tape une requête SQL, ou 'quit' pour sortir) ---")
            while True:
                query = input("\nSQL> ").strip()
                if query.lower() in ("quit", "exit", ""):
                    break
                try:
                    result = await session.call_tool(
                        "executer_requete_sql", {"requete": query}
                    )
                    payload = json.loads(result.content[0].text)
                    print(json.dumps(payload, ensure_ascii=False, indent=2))
                except Exception as error:
                    print(f"Erreur: {error}")


if __name__ == "__main__":
    asyncio.run(main())