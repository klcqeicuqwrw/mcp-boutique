"""Tests automatisés de server.py (base SQLite temporaire, aucune donnée réelle).  Lancer : pytest -q"""
import asyncio
import importlib
import json
import sqlite3

import pytest

DICO = """### DWH_Locataire
*Tiers · exemple*
Locataires.
| Colonne | Type | Clés | Description |
|---|---|---|---|
| `id` | `INTEGER` | PK | Identifiant |
| `nom` | `TEXT` | RGPD | Nom du locataire |
| `ville` | `TEXT` | | Ville |

### DWH_Secret
*Autre · exemple*
Table non autorisée.
| Colonne | Type | Clés | Description |
|---|---|---|---|
| `x` | `TEXT` | | x |
"""


@pytest.fixture()
def srv(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE DWH_Locataire(id INTEGER PRIMARY KEY, nom TEXT, ville TEXT, doc BLOB);
        INSERT INTO DWH_Locataire VALUES (1,'Durand','Lille',x'00ff'),(2,'Martin','Paris',NULL),(3,'Petit','Lille',NULL);
        CREATE TABLE DWH_Secret(x TEXT); INSERT INTO DWH_Secret VALUES ('top');
    """)
    con.commit(); con.close()
    (tmp_path / "dico.md").write_text(DICO, encoding="utf-8")
    monkeypatch.setenv("SQLITE_DB_PATH", str(db))
    monkeypatch.setenv("DICTIONNAIRE_PATH", str(tmp_path / "dico.md"))
    monkeypatch.setenv("MCP_JOURNAL", str(tmp_path / "j.log"))
    monkeypatch.setenv("MCP_TABLES_AUTORISEES", "DWH_Locataire")
    monkeypatch.setenv("MCP_SQL_TIMEOUT", "1")
    monkeypatch.delenv("MCP_BLOQUER_RGPD", raising=False)
    import server
    return importlib.reload(server)


def run(srv, sql):
    return srv._executer(sql, "test")


def test_select_ok(srv):
    r = run(srv, "SELECT ville, COUNT(*) AS n FROM DWH_Locataire GROUP BY ville ORDER BY n DESC")
    assert r["rows"][0] == {"ville": "Lille", "n": 2}


def test_rgpd_bloque_par_defaut(srv):
    assert srv.BLOQUER_RGPD is True
    with pytest.raises(PermissionError):
        run(srv, "SELECT nom FROM DWH_Locataire")
    with pytest.raises(PermissionError):
        run(srv, "SELECT * FROM DWH_Locataire")
    with pytest.raises(PermissionError):  # fuite indirecte via filtre/tri
        run(srv, "SELECT id FROM DWH_Locataire WHERE nom LIKE 'D%'")


def test_rgpd_deblocable(srv, monkeypatch):
    monkeypatch.setenv("MCP_BLOQUER_RGPD", "0")
    srv = importlib.reload(srv)
    assert run(srv, "SELECT nom FROM DWH_Locataire")["row_count"] == 3


@pytest.mark.parametrize("sql", [
    "DELETE FROM DWH_Locataire",
    "WITH t AS (SELECT 1) DELETE FROM DWH_Locataire",
    "INSERT INTO DWH_Locataire(id) VALUES (99)",
    "SELECT 1; DROP TABLE DWH_Locataire",
    "SELECT * FROM sqlite_master",
    "PRAGMA table_info('DWH_Locataire')",
    "ATTACH DATABASE ':memory:' AS x",
    "SELECT x FROM DWH_Secret",                      # hors liste blanche
    "SELECT zeroblob(2000000000)",                    # saturation mémoire
    "SELECT load_extension('x')",
    "",
])
def test_requetes_refusees(srv, sql):
    with pytest.raises((ValueError, PermissionError)):
        run(srv, sql)


def test_donnees_intactes_apres_attaques(srv):
    for sql in ("DELETE FROM DWH_Locataire", "WITH t AS (SELECT 1) DELETE FROM DWH_Locataire"):
        with pytest.raises((ValueError, PermissionError)):
            run(srv, sql)
    assert run(srv, "SELECT COUNT(*) AS n FROM DWH_Locataire")["rows"][0]["n"] == 3


def test_timeout(srv):
    with pytest.raises(TimeoutError):
        run(srv, "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) SELECT COUNT(*) FROM c")


def test_troncature_et_blob(srv):
    r = srv._executer("SELECT id, doc FROM DWH_Locataire ORDER BY id", "t", max_lignes=2)
    assert r["truncated"] and r["row_count"] == 2
    assert r["rows"][0]["doc"] == "<blob 2 octets>"


def test_journal_ecrit(srv, tmp_path):
    run(srv, "SELECT 1")
    ligne = json.loads((tmp_path / "j.log").read_text(encoding="utf-8").splitlines()[-1])
    assert ligne["statut"] == "ok"


def test_outils_async_et_erreurs_lisibles(srv):
    from mcp.server.mcpserver.exceptions import ToolError
    assert asyncio.iscoroutinefunction(srv.executer_requete_sql)
    out = json.loads(asyncio.run(srv.lister_tables()))
    assert [t["table"] for t in out["tables"]] == ["DWH_Locataire"]
    with pytest.raises(ToolError, match="Table inconnue"):
        asyncio.run(srv.decrire_table("nimportequoi"))
    with pytest.raises(ToolError, match="interdite|refus"):
        asyncio.run(srv.executer_requete_sql("SELECT nom FROM DWH_Locataire"))


def test_decrire_table_marque_rgpd(srv):
    d = json.loads(asyncio.run(srv.decrire_table("DWH_Locataire")))
    assert any(c["nom"] == "nom" and c.get("bloquee") for c in d["colonnes"])


def test_apercu_exclut_colonnes_rgpd(srv):
    r = json.loads(asyncio.run(srv.apercu_table("DWH_Locataire", 2)))
    assert "nom" not in r["columns"]


def test_dictionnaire_recharge_si_modifie(srv, tmp_path):
    assert "dwh_secret" in srv._dico()
    import os, time
    p = tmp_path / "dico.md"
    p.write_text(DICO.split("### DWH_Secret")[0], encoding="utf-8")
    os.utime(p, (time.time() + 5, time.time() + 5))
    assert "dwh_secret" not in srv._dico()