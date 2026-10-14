"""Parcours HTTP sur bases temporaires, sans clé ni appel Gemini."""
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def web(tmp_path, monkeypatch):
    import securite as S
    from boutique import chat
    from main import app

    monkeypatch.setattr(S, "APP_DB", tmp_path / "app.db")
    monkeypatch.setattr(S, "DATABASE_PATH", tmp_path / "metier.db")
    monkeypatch.setenv("ADMIN_PASSWORD", "administrateur-test")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    S._schema_cache.clear()
    S._echecs.clear()
    chat._sql_cache.clear()
    with sqlite3.connect(S.DATABASE_PATH) as c:
        c.executescript("""
        CREATE TABLE Patrimoine(ID_patrimoine TEXT, Libelle_patrimoine TEXT,
            Libelle_commune TEXT, Latitude TEXT, Longitude TEXT, Adresse TEXT);
        INSERT INTO Patrimoine VALUES('P1','Résidence A','Lille','50,63','3.06','SECRET');
        INSERT INTO Patrimoine VALUES('P2','Résidence B','Paris','0','0','SECRET');
        CREATE TABLE Client(ID_client TEXT, ID_client_lot TEXT, Nom_prenom_client TEXT);
        INSERT INTO Client VALUES('C1','CL1','Alice'),('C1','CL2','Alice'),('C2','CL3','Bob');
        CREATE TABLE Commande(ID_commande TEXT, Montant_HT REAL);
        INSERT INTO Commande VALUES('CMD1',100),('CMD2',200);
        CREATE TABLE Intervention(ID_intervention TEXT, ID_commande TEXT);
        INSERT INTO Intervention VALUES('I1','CMD1'),('I2','CMD1'),('I3','CMD2');
        """)
    dico = tmp_path / "dico.md"
    dico.write_text("""## Client
- ID_client — Type SQLite : TEXT.
   Description : Identifiant du client
- ID_client_lot — Type SQLite : TEXT.
- Nom_prenom_client — Type SQLite : TEXT.
   Confidentialité : RGPD
   Description : Nom du client
## Secret
- Salaire — Type SQLite : REAL.
   Description : Salaire confidentiel
""", encoding="utf-8")
    monkeypatch.setattr(chat, "DICTIONNAIRE_PATH", dico)
    with TestClient(app, headers={"X-Requested-With": "fetch"}) as client:
        sid = S.q("SELECT id FROM services ORDER BY id", one=True)["id"]
        S.q("INSERT INTO permissions VALUES(?,?,NULL)", (sid, "Client"), write=True)
        S.q("INSERT INTO permissions VALUES(?,?,NULL)", (sid, "Patrimoine"), write=True)
        uid = S.creer_utilisateur("alice", "motdepasse-test", service_id=sid)
        S.creer_utilisateur("bob", "motdepasse-test", service_id=sid)
        calls = []

        def generer(question, schema, historique, **kwargs):
            calls.append(dict(question=question, schema=schema, historique=historique, **kwargs))
            return "SELECT ID_client, Nom_prenom_client FROM Client"

        monkeypatch.setattr(chat, "generer_sql", generer)
        monkeypatch.setattr(chat, "formuler_reponse", lambda *a, **kw: "Réponse de test")
        yield SimpleNamespace(client=client, S=S, sid=sid, uid=uid, calls=calls, chat=chat)
    S._schema_cache.clear()
    chat._sql_cache.clear()


def connecter(web, username="alice", password="motdepasse-test"):
    r = web.client.post("/api/login", json=dict(username=username, password=password))
    assert r.status_code == 200, r.text
    return r


def poser(web):
    cid = web.client.post("/api/conversations").json()["id"]
    r = web.client.post("/api/ask", json=dict(conv_id=cid, question="Liste des clients"))
    assert r.status_code == 200, r.text
    return cid, r.json()["id"]


def test_authentification_et_csrf(web):
    assert web.client.get("/api/conversations").status_code == 401
    assert web.client.post("/api/login", json={"username": "alice", "password": "faux"}).status_code == 401
    r = connecter(web)
    assert "HttpOnly" in r.headers["set-cookie"]
    assert "SameSite=strict" in r.headers["set-cookie"]
    assert web.client.get("/api/admin/users").status_code == 403
    web.client.headers.pop("X-Requested-With")
    assert web.client.post("/api/conversations").status_code == 403


def test_isolation_conversations_exports_et_texte(web):
    connecter(web)
    cid, mid = poser(web)
    assert web.client.get(f"/api/export/{mid}").status_code == 200
    connecter(web, "bob")
    assert web.client.get(f"/api/conversations/{cid}").status_code == 404
    assert web.client.get(f"/api/export/{mid}").status_code == 404
    assert web.client.post(f"/api/ask/{mid}/texte").status_code == 404


def test_retrait_colonne_masque_anciens_resultats_et_contexte(web):
    connecter(web)
    cid, mid = poser(web)
    web.S.q("UPDATE permissions SET columns=? WHERE service_id=? AND table_name='Client'",
            (json.dumps(["ID_client"]), web.sid), write=True)
    r = web.client.get(f"/api/conversations/{cid}")
    ancien = r.json()["messages"][0]
    assert ancien["resultats"] is None and ancien["reponse"] is None and ancien["sql_genere"] is None
    assert "Alice" not in r.text
    assert web.client.get(f"/api/export/{mid}").status_code == 403
    assert web.client.post(f"/api/ask/{mid}/texte").status_code == 403
    web.client.post("/api/ask", json=dict(conv_id=cid, question="Liste après retrait"))
    assert not web.calls[-1]["historique"]
    assert "Nom_prenom_client" not in web.calls[-1]["schema"]
    assert "Nom_prenom_client" not in web.calls[-1]["dictionnaire"]
    assert "Salaire" not in web.calls[-1]["dictionnaire"]


def test_changement_service_et_legacy(web):
    connecter(web)
    cid, mid = poser(web)
    web.S.q("UPDATE messages SET access_scope=NULL WHERE id=?", (mid,), write=True)
    assert web.client.get(f"/api/export/{mid}").status_code == 200
    assert web.client.get(f"/api/conversations/{cid}").json()["messages"][0]["resultats"] is not None
    assert web.client.post(f"/api/ask/{mid}/texte").status_code == 200
    web.S.q("UPDATE users SET service_id=NULL WHERE id=?", (web.uid,), write=True)
    assert web.client.get(f"/api/conversations/{cid}").json()["messages"][0]["resultats"] is None
    assert web.client.post("/api/ask", json=dict(conv_id=cid, question="Clients")).status_code == 403


def test_admin_retrouve_resultat_legacy_meme_si_ancien_schema(web):
    connecter(web, "admin", "administrateur-test")
    cid, mid = poser(web)
    web.S.q("UPDATE messages SET access_scope=NULL, sql='SELECT nom FROM ancienne_table' WHERE id=?", (mid,), write=True)
    assert web.client.get(f"/api/conversations/{cid}").json()["messages"][0]["resultats"] is not None
    assert web.client.get(f"/api/export/{mid}").status_code == 200


def test_legacy_respecte_retrait_permissions(web):
    connecter(web)
    cid, mid = poser(web)
    web.S.q("UPDATE messages SET access_scope=NULL WHERE id=?", (mid,), write=True)
    web.S.q("UPDATE permissions SET columns=? WHERE service_id=? AND table_name='Client'",
            (json.dumps(["ID_client"]), web.sid), write=True)
    assert web.client.get(f"/api/export/{mid}").status_code == 403
    assert web.client.get(f"/api/conversations/{cid}").json()["messages"][0]["resultats"] is None


@pytest.mark.parametrize("contenu", ["{cassé", "[]", '{"columns": [], "rows": [42]}'])
def test_resultat_abime_ne_casse_pas_conversation(web, contenu):
    connecter(web)
    cid, mid = poser(web)
    web.S.q("UPDATE messages SET resultats=? WHERE id=?", (contenu, mid), write=True)
    r = web.client.get(f"/api/conversations/{cid}")
    assert r.status_code == 200
    assert r.json()["messages"][0]["resultats"] is None
    assert web.client.get(f"/api/export/{mid}").status_code == 409
    assert web.client.post(f"/api/ask/{mid}/texte").status_code == 409


@pytest.mark.parametrize("texte", ["", "pas du JSON", "[]", "{}", '{"sql": 123}', '{"sql": "  "}'])
def test_reponse_gemini_malformee(monkeypatch, texte):
    import api
    monkeypatch.setattr(api, "_appeler_et_journaliser", lambda *a: SimpleNamespace(text=texte))
    with pytest.raises(ValueError, match="Gemini"):
        api.generer_sql("Question", "Schema", [])


def test_retry_gemini_reseau_et_pas_attente_apres_dernier_echec(monkeypatch):
    import api
    import httpx
    appels, pauses = [], []
    def erreur(**kwargs):
        appels.append(kwargs)
        raise httpx.ConnectError("Connexion interrompue")
    monkeypatch.setattr(api, "obtenir_client", lambda: SimpleNamespace(models=SimpleNamespace(generate_content=erreur)))
    monkeypatch.setattr(api.time, "sleep", pauses.append)
    with pytest.raises(httpx.ConnectError):
        api._appeler_gemini_avec_retry("Question", api.types.GenerateContentConfig(), tentatives=3)
    assert len(appels) == 3 and pauses == [1.5, 3]


@pytest.mark.parametrize("code", [504, None])
def test_expiration_gemini_sans_repetition(monkeypatch, code):
    import api
    import httpx
    appels = []
    class DeadlineError(Exception):
        pass
    erreur = DeadlineError("DEADLINE_EXCEEDED") if code else httpx.ReadTimeout("Temps dépassé")
    erreur.code = code
    def echouer(**kwargs):
        appels.append(kwargs)
        raise erreur
    monkeypatch.setattr(api, "obtenir_client", lambda: SimpleNamespace(models=SimpleNamespace(generate_content=echouer)))
    monkeypatch.setattr(api.time, "sleep", lambda _: pytest.fail("Aucune attente après expiration"))
    with pytest.raises(type(erreur)):
        api._appeler_gemini_avec_retry("Question", api.types.GenerateContentConfig())
    assert len(appels) == 1


def test_delai_gemini_par_defaut_et_configurable(monkeypatch):
    import api
    monkeypatch.delenv("GEMINI_TIMEOUT_SECONDS", raising=False)
    assert api.options_http().timeout == 20000
    assert api.options_http().retry_options.attempts == 1
    monkeypatch.setenv("GEMINI_TIMEOUT_SECONDS", "180")
    assert api.options_http().timeout == 180000
    monkeypatch.setenv("GEMINI_TIMEOUT_SECONDS", "invalide")
    with pytest.raises(ValueError, match="GEMINI_TIMEOUT_SECONDS"):
        api.options_http()


def test_texte_recoit_sql_execute(web, monkeypatch):
    connecter(web)
    _, mid = poser(web)
    appels = []
    monkeypatch.setattr(web.chat, "formuler_reponse", lambda *a, **kw: appels.append(kw) or "Texte")
    assert web.client.post(f"/api/ask/{mid}/texte").status_code == 200
    assert appels[0]["sql"] == "SELECT ID_client, Nom_prenom_client FROM Client"


def test_exports_csv_proteges_et_json_fidele(web, monkeypatch):
    connecter(web)
    monkeypatch.setattr(web.chat, "generer_sql", lambda *a, **kw: "SELECT '=1+1' AS formule, NULL AS vide")
    _, mid = poser(web)
    csv = web.client.get(f"/api/export/{mid}?format=csv")
    assert "'=1+1" in csv.text
    assert csv.headers["cache-control"] == "no-store"
    assert web.client.get(f"/api/export/{mid}?format=json").json() == [{"formule": "=1+1", "vide": None}]


@pytest.mark.parametrize("format,signature", [("pdf", b"%PDF"), ("xlsx", b"PK"), ("md", b"| "), ("tsv", b"\xef\xbb\xbf")])
def test_formats_export(web, format, signature):
    connecter(web)
    _, mid = poser(web)
    r = web.client.get(f"/api/export/{mid}?format={format}")
    assert r.status_code == 200, r.text
    assert r.content.startswith(signature)


def test_carte_nouveau_schema_et_permissions(web):
    connecter(web)
    r = web.client.get("/api/carte")
    assert r.status_code == 200, r.text
    assert r.json()["points"] == [dict(id="P1", nom="Résidence A", commune="Lille", lat=50.63, lon=3.06)]
    assert r.json()["ignores"] == 1
    assert "SECRET" not in r.text
    web.S.q("DELETE FROM permissions WHERE table_name='Patrimoine' AND service_id=?", (web.sid,), write=True)
    assert web.client.get("/api/carte").status_code == 403


def test_permissions_invalides_ne_suppriment_pas_les_droits(web):
    connecter(web, "admin", "administrateur-test")
    avant = web.S.q("SELECT * FROM permissions WHERE service_id=?", (web.sid,))
    r = web.client.put(f"/api/admin/services/{web.sid}/permissions", json=[
        dict(table="Client", columns=["ID_client"]), dict(table="Inconnue")])
    assert r.status_code == 400
    assert web.S.q("SELECT * FROM permissions WHERE service_id=?", (web.sid,)) == avant


def test_changement_droits_pendant_generation(web, monkeypatch):
    connecter(web)
    cid = web.client.post("/api/conversations").json()["id"]
    def changement(*a, **kw):
        web.S.q("DELETE FROM permissions WHERE service_id=?", (web.sid,), write=True)
        return "SELECT Nom_prenom_client FROM Client"
    monkeypatch.setattr(web.chat, "generer_sql", changement)
    r = web.client.post("/api/ask", json=dict(conv_id=cid, question="Clients"))
    assert r.status_code == 403 and "Alice" not in r.text


@pytest.mark.parametrize("question,sql,attendu", [
    ("Combien de clients distincts ?", "SELECT COUNT(DISTINCT ID_client) AS n FROM Client", {"nombre": 2}),
    ("Montant des commandes ayant une intervention ?", "SELECT SUM(Montant_HT) AS total FROM Commande c WHERE EXISTS (SELECT 1 FROM Intervention i WHERE i.ID_commande=c.ID_commande)", {"total": 300}),
])
def test_questions_metier_reference(web, monkeypatch, question, sql, attendu):
    # Références déterministes : vérifient l'orchestration et les pièges de grain.
    # La qualité réelle du modèle doit être évaluée séparément avec une clé Gemini.
    connecter(web, "admin", "administrateur-test")
    monkeypatch.setattr(web.chat, "generer_sql", lambda *a, **kw: sql)
    cid = web.client.post("/api/conversations").json()["id"]
    r = web.client.post("/api/ask", json=dict(conv_id=cid, question=question))
    assert r.status_code == 200, r.text
    assert r.json()["resultats"]["rows"] == [attendu]


def test_aucune_api_alternative_non_authentifiee(web):
    import api
    assert not hasattr(api, "app")
    assert web.client.post("/ask", json={"question": "Clients"}).status_code == 404


def test_migration_preserve_anciens_messages(tmp_path, monkeypatch):
    import securite as S
    monkeypatch.setattr(S, "APP_DB", tmp_path / "ancien.db")
    monkeypatch.setenv("ADMIN_PASSWORD", "administrateur-test")
    with sqlite3.connect(S.APP_DB) as c:
        c.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY, conv_id TEXT, question TEXT, reponse TEXT, sql TEXT, resultats TEXT, erreur TEXT, created_at REAL)")
        c.execute("INSERT INTO messages(id,question) VALUES(1,'Question conservée')")
    S.init_db()
    S.init_db()
    m = S.q("SELECT * FROM messages WHERE id=1", one=True)
    assert m["question"] == "Question conservée" and m["access_scope"] is None


def test_synthese_sql_apercu_et_troncature(monkeypatch):
    import api
    prompts = []
    monkeypatch.setattr(api, "_appeler_et_journaliser", lambda kind, prompt, *a: prompts.append(prompt) or SimpleNamespace(text="Résumé"))
    res = dict(columns=["x"], rows=[{"x": i} for i in range(500)], row_count=500, truncated=True)
    texte = api.formuler_reponse("Explique cette liste", res, sql="SELECT x FROM exemple")
    assert "total inconnu" in texte
    assert "SELECT x FROM exemple" in prompts[0]
    assert '"total_lignes": null' in prompts[0]
    assert '"x": 19' in prompts[0] and '"x": 20' not in prompts[0]


def test_comptage_direct_sans_appel_gemini(web, monkeypatch):
    connecter(web)
    monkeypatch.setattr(web.chat, "generer_sql", lambda *a, **kw: pytest.fail("Ce comptage ne doit pas appeler Gemini"))
    cid = web.client.post("/api/conversations").json()["id"]
    r = web.client.post("/api/ask", json=dict(conv_id=cid, question="Combien de clients distincts y a-t-il ?"))
    assert r.status_code == 200, r.text
    assert r.json()["resultats"]["rows"] == [{"nombre": 2}]
    assert not web.calls


def test_comptage_filtre_ne_perd_pas_condition(web, monkeypatch):
    connecter(web)
    cid = web.client.post("/api/conversations").json()["id"]
    r = web.client.post("/api/ask", json=dict(conv_id=cid, question="Combien de clients à Rennes ?"))
    assert r.status_code == 200
    assert len(web.calls) == 1


def test_synthese_simple_locale_sans_gemini(monkeypatch):
    import api
    monkeypatch.setattr(api, "_appeler_et_journaliser", lambda *a: pytest.fail("Aucun appel pour un résultat simple"))
    res = dict(columns=["nombre"], rows=[{"nombre": 320}], row_count=1, truncated=False)
    assert api.formuler_reponse("Combien de clients ?", res) == "Résultat : 320."
    res = dict(columns=["nom"], rows=[{"nom": "A"}, {"nom": "B"}], row_count=2, truncated=False)
    assert "2 lignes" in api.formuler_reponse("Liste les clients", res)


@pytest.mark.parametrize("question,type_attendu", [("Camembert par commune", "pie"), ("Courbe du total", "line"), ("Barres par commune", "bar")])
def test_graphique_local(question, type_attendu):
    from boutique.graphiques import choisir_graphique
    res = dict(columns=["commune", "total"], rows=[dict(commune="Rennes", total=10), dict(commune="Nantes", total=12)])
    spec = choisir_graphique(question, res)
    assert spec["type"] == type_attendu and spec["x"] == "commune" and spec["y"] == ["total"]
