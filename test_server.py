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
| `doc` | `BLOB` | | Document de test |

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


def test_sortie_markdown_par_defaut(srv):
    out = asyncio.run(srv.executer_requete_sql("SELECT ville, COUNT(*) AS n FROM DWH_Locataire GROUP BY ville ORDER BY ville"))
    assert out.startswith("| ville | n |\n|---|---|\n| Lille | 2 |\n| Paris | 1 |")
    assert "2 ligne(s)" in out


def test_sortie_json_sur_demande(srv):
    out = asyncio.run(srv.executer_requete_sql("SELECT 1 AS a", format="json"))
    assert json.loads(out)["rows"] == [{"a": 1}]


def test_markdown_echappe_les_pipes(srv):
    out = asyncio.run(srv.executer_requete_sql("SELECT 'a|b' || char(10) || 'c' AS t"))
    assert "a\\|b c" in out


def test_format_invalide(srv):
    from mcp.server.mcpserver.exceptions import ToolError
    with pytest.raises(ToolError, match="format"):
        asyncio.run(srv.executer_requete_sql("SELECT 1", format="xml"))


def test_alias_distincts_sans_perte(srv):
    r=run(srv,'SELECT 1 AS a, 2 AS a, 3 AS a_2, 4 AS a')
    assert len(set(r['columns']))==4
    assert list(r['rows'][0].values())==[1,2,3,4]
    assert r['rows'][0]['a_2']==3


def test_une_ligne_enorme_est_refusee(srv,monkeypatch):
    monkeypatch.setattr(srv,'MAX_CHARS',1000)
    with pytest.raises(ValueError,match='ligne dépasse'):
        run(srv,"SELECT printf('%.*c',5000,'x') AS texte")


@pytest.mark.parametrize('format',['json','markdown'])
def test_reponse_bornee_meme_avec_echappement(srv,monkeypatch,format):
    monkeypatch.setattr(srv,'MAX_CHARS',1000)
    out=asyncio.run(srv.executer_requete_sql("WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c WHERE x<100) SELECT x, printf('%.*c',50,'|') AS t FROM c",format))
    assert len(out)<=1000
    if format=='json':
        r=json.loads(out)
        assert r['truncated'] and 0<r['row_count']<100
    else:
        assert 'tronqué' in out


def test_sql_trop_volumineux(srv,monkeypatch):
    monkeypatch.setattr(srv,'MAX_SQL_CHARS',1000)
    with pytest.raises(ValueError,match='volumineuse'):
        run(srv,"SELECT '"+'x'*1000+"'")


def test_colonne_ajoutee_non_documentee_bloquee(srv):
    with sqlite3.connect(srv.DB_PATH) as con:
        con.execute('ALTER TABLE DWH_Locataire ADD COLUMN telephone TEXT')
        con.execute("UPDATE DWH_Locataire SET telephone='secret'")
    with pytest.raises(PermissionError):
        run(srv,'SELECT telephone FROM DWH_Locataire')
    out=json.loads(asyncio.run(srv.apercu_table('DWH_Locataire')))
    assert 'telephone' not in out['columns']


def test_dictionnaire_supprime_en_cours_bloque(srv):
    srv.DICO_PATH.unlink()
    with pytest.raises(PermissionError,match='Protection RGPD'):
        run(srv,'SELECT ville FROM DWH_Locataire')


def test_faute_configuration_rgpd_ne_desactive_pas(srv,monkeypatch):
    monkeypatch.setenv('MCP_BLOQUER_RGPD','treu')
    assert srv._booleen('MCP_BLOQUER_RGPD',True) is True


def test_table_autorisee_inexistante(srv,monkeypatch):
    monkeypatch.setattr(srv,'TABLES_AUTORISEES',{'dwh_inexistante'})
    with pytest.raises(SystemExit,match='introuvables'):
        srv.verifier_demarrage()


@pytest.mark.parametrize('config',[
    {'MCP_TRANSPORT':'sdtio'},
    {'MCP_TRANSPORT':'http','MCP_HOST':'0.0.0.0'},
    {'MCP_TRANSPORT':'http','MCP_HOST':'127.0.0.1','MCP_PORT':'invalid'},
    {'MCP_TRANSPORT':'http','MCP_HOST':'127.0.0.1','MCP_PORT':'65536'},
])
def test_demarrage_invalide_refuse(srv,monkeypatch,config):
    for k,v in config.items():
        monkeypatch.setenv(k,v)
    with pytest.raises(SystemExit):
        srv.lancer()


def test_demarrage_http_sdk_installe_transmet_port(srv,monkeypatch):
    monkeypatch.setenv('MCP_TRANSPORT','http')
    monkeypatch.setenv('MCP_HOST','127.0.0.1')
    monkeypatch.setenv('MCP_PORT','8765')
    appels=[]
    monkeypatch.setattr(srv.mcp,'run',lambda *a,**kw:appels.append((a,kw)))
    srv.lancer()
    assert appels==[(('streamable-http',),{'host':'127.0.0.1','port':8765})]


def test_annulation_libere_vraiment_le_travail(srv,monkeypatch):
    import threading
    import time
    places=threading.BoundedSemaphore(1)
    monkeypatch.setattr(srv,'_places',places)
    monkeypatch.setattr(srv,'SQL_TIMEOUT',10)
    demarre,fini=threading.Event(),threading.Event()
    @srv._lisible
    def long():
        try:
            demarre.set()
            run(srv,'WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) SELECT COUNT(*) FROM c')
            return 'inattendu'
        finally:
            fini.set()
    async def scenario():
        appel=asyncio.create_task(long())
        while not demarre.is_set():
            await asyncio.sleep(.005)
        appel.cancel()
        with pytest.raises(asyncio.CancelledError):
            await appel
        limite=time.monotonic()+3
        while not fini.is_set() and time.monotonic()<limite:
            await asyncio.sleep(.005)
        assert fini.is_set(), 'Le calcul SQL doit arreter avant son timeout normal'
        acquis=places.acquire(blocking=False)
        while not acquis and time.monotonic()<limite:
            await asyncio.sleep(.005)
            acquis=places.acquire(blocking=False)
        assert acquis
        places.release()
    asyncio.run(scenario())


def test_surcharge_refusee(srv,monkeypatch):
    import threading
    places=threading.BoundedSemaphore(1)
    places.acquire()
    monkeypatch.setattr(srv,'_places',places)
    with pytest.raises(srv.ToolError,match='occupé'):
        asyncio.run(srv.lister_tables())
    places.release()


def test_metadonnees_trop_grandes(srv,monkeypatch):
    monkeypatch.setattr(srv,'MAX_CHARS',10)
    with pytest.raises(srv.ToolError,match='taille de réponse'):
        asyncio.run(srv.lister_tables())


def test_recherche_ignore_colonne_supprimee(srv):
    with sqlite3.connect(srv.DB_PATH) as con:
        con.execute('ALTER TABLE DWH_Locataire DROP COLUMN ville')
    r=json.loads(asyncio.run(srv.rechercher_colonnes('ville')))
    assert r['total_trouve']==0


def test_protocole_stdio_reel(srv):
    """Initialisation, découverte et erreurs via les vrais messages MCP."""
    import os
    import sys
    from pathlib import Path
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    async def scenario():
        root=Path(__file__).resolve().parent
        env=dict(os.environ,SQLITE_DB_PATH=str(srv.DB_PATH),DICTIONNAIRE_PATH=str(srv.DICO_PATH),
                 MCP_JOURNAL='',MCP_BLOQUER_RGPD='1',MCP_TRANSPORT='stdio')
        params=StdioServerParameters(command=sys.executable,args=[str(root/'server.py')],cwd=str(root),env=env)
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                liste=await session.list_tools()
                assert {t.name for t in liste.tools}=={'lister_tables','rechercher_colonnes','decrire_table',
                    'apercu_table','valeurs_distinctes','executer_requete_sql'}
                for t in liste.tools:
                    assert t.annotations.read_only_hint
                resultat=await session.call_tool('executer_requete_sql',{'requete':'SELECT ville FROM DWH_Locataire','format':'json'})
                assert not resultat.is_error
                assert json.loads(resultat.content[0].text)['row_count']==3
                for sql in ['SELECT nom FROM DWH_Locataire','DELETE FROM DWH_Locataire','SELECT x FROM DWH_Secret']:
                    refus=await session.call_tool('executer_requete_sql',{'requete':sql})
                    assert refus.is_error
                    assert 'top' not in refus.content[0].text and 'Durand' not in refus.content[0].text
                # Une erreur d'outil ne doit pas casser la session.
                suite=await session.call_tool('lister_tables',{})
                assert not suite.is_error
    asyncio.run(asyncio.wait_for(scenario(),timeout=20))
