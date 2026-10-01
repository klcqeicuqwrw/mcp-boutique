"""
Tests automatiques de server.py (pytest) : sécurité, limites, démarrage.

Usage :  pip install pytest   puis   pytest -v
Les tests construisent une petite base et un petit dictionnaire temporaires :
aucune donnée réelle n'est utilisée.
"""
import asyncio
import importlib
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="mcp_test_"))
_DB = _TMP / "test.db"
_DICO = _TMP / "dico.md"

con = sqlite3.connect(_DB)
con.executescript("""
CREATE TABLE DWH_Client (ID INTEGER PRIMARY KEY, Nom TEXT, Ville TEXT, Loyer REAL);
INSERT INTO DWH_Client VALUES (1,'Dupont','Lorient',420.5),(2,'Martin','Vannes',380),(3,'Durand','Lorient',510);
CREATE TABLE DWH_Lot (ID INTEGER PRIMARY KEY, Adresse TEXT);
INSERT INTO DWH_Lot VALUES (1,'1 rue A');
CREATE VIEW V_Client AS SELECT * FROM DWH_Client;
""")
con.commit()
con.close()

_DICO.write_text("""# Dictionnaire
### DWH_Client
*Clients · test*
Clients du bailleur.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID` | `int` | PK | Identifiant. |
| `Nom` | `nvarchar(50)` | RGPD | Nom du client. |
| `Ville` | `nvarchar(50)` |  | Ville. |
| `Loyer` | `float` |  | Loyer. |

### DWH_Lot
*Patrimoine · test*
Logements.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID` | `int` | PK | Identifiant. |
| `Adresse` | `nvarchar(50)` |  | Adresse. |
""", encoding="utf-8")

os.environ.update({
    "SQLITE_DB_PATH": str(_DB),
    "DICTIONNAIRE_PATH": str(_DICO),
    "MCP_JOURNAL": str(_TMP / "journal.log"),
    "MCP_BLOQUER_RGPD": "1",
})
sys.path.insert(0, str(Path(__file__).parent))
server = importlib.import_module("server")


def executer(sql):
    return server._executer(sql, "test")


def refuse(sql):
    """La requête doit lever une erreur (PermissionError, ValueError, TimeoutError...)."""
    with pytest.raises((PermissionError, ValueError, TimeoutError)):
        executer(sql)


# --------------------------------------------------------------------------- requêtes normales
def test_select_simple():
    r = executer("SELECT COUNT(*) AS nb FROM DWH_Client")
    assert r["rows"] == [{"nb": 3}]


def test_agregat_avec_colonne_non_rgpd():
    r = executer("SELECT Ville, SUM(Loyer) AS total FROM DWH_Client GROUP BY Ville ORDER BY Ville")
    assert [x["Ville"] for x in r["rows"]] == ["Lorient", "Vannes"]


def test_troncature(monkeypatch):
    r = server._executer("SELECT ID, Ville FROM DWH_Client", "test", max_lignes=2)
    assert r["truncated"] is True and r["row_count"] == 2


# --------------------------------------------------------------------------- doit être refusé
@pytest.mark.parametrize("sql", [
    "DELETE FROM DWH_Client",
    "UPDATE DWH_Client SET Loyer = 0",
    "DROP TABLE DWH_Client",
    "INSERT INTO DWH_Lot VALUES (9,'x')",
    "SELECT 1; DROP TABLE DWH_Client",
    "WITH x AS (SELECT 1) DELETE FROM DWH_Client",
    "WITH x AS (SELECT 1) INSERT INTO DWH_Lot VALUES (9,'x')",
    "SELECT * FROM sqlite_master",
    "PRAGMA table_info('DWH_Client')",
    "ATTACH DATABASE ':memory:' AS m",
    "SELECT load_extension('x')",
    "",
    "   ;  ",
])
def test_requetes_interdites(sql):
    refuse(sql)


def test_la_base_n_a_pas_change():
    refuse("DELETE FROM DWH_Client")
    assert executer("SELECT COUNT(*) AS nb FROM DWH_Client")["rows"][0]["nb"] == 3


# --------------------------------------------------------------------------- RGPD
@pytest.mark.parametrize("sql", [
    "SELECT Nom FROM DWH_Client",
    "SELECT * FROM DWH_Client",
    "SELECT Nom AS x FROM DWH_Client",
    "SELECT x FROM (SELECT Nom AS x FROM DWH_Client)",
    "WITH c AS (SELECT Nom FROM DWH_Client) SELECT * FROM c",
    "SELECT Ville FROM DWH_Client WHERE Nom = 'Dupont'",   # filtrer sur une colonne RGPD = la lire
    "SELECT COUNT(*) FROM DWH_Client GROUP BY Nom",
    "SELECT Nom FROM V_Client",                              # via une vue
    "SELECT * FROM V_Client",
])
def test_colonnes_rgpd_bloquees(sql):
    refuse(sql)


def test_rgpd_debloquable(monkeypatch):
    monkeypatch.setattr(server, "BLOQUER_RGPD", False)
    assert executer("SELECT Nom FROM DWH_Client WHERE ID = 1")["rows"] == [{"Nom": "Dupont"}]


# --------------------------------------------------------------------------- tables autorisées
def test_tables_autorisees(monkeypatch):
    monkeypatch.setattr(server, "TABLES_AUTORISEES", {"dwh_lot"})
    assert executer("SELECT COUNT(*) AS nb FROM DWH_Lot")["rows"][0]["nb"] == 1
    refuse("SELECT COUNT(*) FROM DWH_Client")


# --------------------------------------------------------------------------- limites de ressources
def test_bombe_memoire_zeroblob():
    refuse("SELECT length(zeroblob(2000000000))")


def test_bombe_memoire_randomblob():
    refuse("SELECT length(randomblob(2000000000))")


def test_requete_trop_longue(monkeypatch):
    monkeypatch.setattr(server, "SQL_TIMEOUT", 0.5)
    with pytest.raises(TimeoutError):
        executer("WITH RECURSIVE c(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM c) "
                 "SELECT COUNT(*) FROM c")


def test_sql_geant():
    refuse("SELECT " + "1+" * 30000 + "1")


# --------------------------------------------------------------------------- enveloppe des outils
def test_erreur_lisible_pour_l_assistant():
    from server import ToolError
    with pytest.raises(ToolError) as e:
        asyncio.run(server.executer_requete_sql("SELECT Nom FROM DWH_Client"))
    assert "refus" in str(e.value).lower()


def test_outil_decrire_table():
    import json
    d = json.loads(asyncio.run(server.decrire_table("dwh_client")))
    assert d["table"] == "DWH_Client"
    assert next(c for c in d["colonnes"] if c["nom"] == "Nom")["rgpd"] is True


def test_table_inconnue_message_utile():
    from server import ToolError
    with pytest.raises(ToolError) as e:
        asyncio.run(server.decrire_table("client_inexistant"))
    assert "Table inconnue" in str(e.value)


def test_apercu_sans_colonnes_rgpd():
    import json
    r = json.loads(asyncio.run(server.apercu_table("DWH_Client", 2)))
    assert "Nom" not in r["columns"]


# --------------------------------------------------------------------------- journal et démarrage
def test_journal_ecrit_et_tronque(monkeypatch):
    monkeypatch.setattr(server, "JOURNAL_SQL_MAX", 50)
    executer("SELECT COUNT(*) AS nb FROM DWH_Client WHERE Ville = '" + "x" * 200 + "'")
    contenu = (_TMP / "journal.log").read_text(encoding="utf-8")
    assert "car.)" in contenu


def test_demarrage_ok():
    # seule la vue de test (absente du dictionnaire) doit être signalée
    assert all("v_client" in a for a in server.verifier_demarrage())


def test_demarrage_signale_table_hors_dictionnaire(monkeypatch):
    c = sqlite3.connect(_DB)
    c.execute("CREATE TABLE DWH_Nouvelle (ID INTEGER, Nom TEXT)")
    c.commit()
    c.close()
    try:
        avertissements = server.verifier_demarrage()
        assert any("DWH_Nouvelle".lower() in a.lower() for a in avertissements)
    finally:
        c = sqlite3.connect(_DB)
        c.execute("DROP TABLE DWH_Nouvelle")
        c.commit()
        c.close()


def test_demarrage_refuse_si_rgpd_sans_dictionnaire(monkeypatch):
    monkeypatch.setattr(server, "DICO_PATH", _TMP / "absent.md")
    with pytest.raises(SystemExit):
        server.verifier_demarrage()