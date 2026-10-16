"""Les deux parcours complets, vraie base en lecture seule et API IA indisponible."""
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from boutique.requetes_metier import reconnaitre


ROOT = Path(__file__).parent
SCENARIO_1 = ["J'ai un contrôle ANCOLS qui arrive, peux-tu m'aider ?",
              "Donne moi la liste des clients moraux"]
SCENARIO_2 = [
    "Donnes moi les patrimoines avec une lettre DPE de DPE F ou G ?",
    "Donne moi les personnes de plus de 65 ans qui vivent dans ces logements",
    "Parmi ces gens là, donne moi ceux qui habitent au moins au 2 eme étage sans ascenseur",
    "Parmi ces gens là donne moi dans l'ordre croissant le dernier contact que l'on a eu avec eux. "
    "Je veux aussi pouvoir les contacter et les localiser",
]


@pytest.fixture
def demo(tmp_path, monkeypatch):
    import api
    import securite as S
    from boutique import chat
    from main import app

    monkeypatch.setattr(S, 'APP_DB', tmp_path / 'app.db')
    monkeypatch.setattr(S, 'DATABASE_PATH', ROOT / 'DWH_fictive_10000_lignes.sqlite')
    monkeypatch.setenv('ADMIN_USERNAME', 'demo-admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'administrateur-test')
    S._schema_cache.clear()
    S._echecs.clear()
    chat._sql_cache.clear()
    appels = []
    def indisponible(*args, **kwargs):
        appels.append(kwargs)
        raise RuntimeError('503 UNAVAILABLE : fournisseur indisponible pendant la démonstration')
    monkeypatch.setattr(chat, 'generer_sql', indisponible)
    monkeypatch.setattr(chat, 'formuler_reponse', indisponible)
    monkeypatch.setattr(api, 'obtenir_client', indisponible)
    monkeypatch.setattr(api, 'obtenir_client_openai', indisponible)
    monkeypatch.setattr(api, 'obtenir_client_groq', indisponible)
    with TestClient(app, headers={'X-Requested-With': 'fetch'}) as client:
        sid = S.q('SELECT id FROM services ORDER BY id', one=True)['id']
        for table in S.tables_info():
            S.q('INSERT INTO permissions VALUES(?,?,NULL)', (sid, table), write=True)
        S.creer_utilisateur('demo', 'demonstration-test', service_id=sid)
        assert client.post('/api/login', json=dict(username='demo', password='demonstration-test')).status_code == 200
        yield SimpleNamespace(client=client, S=S, sid=sid, appels=appels)
    S._schema_cache.clear()
    chat._sql_cache.clear()


def envoyer(demo, cid, question, **options):
    r = demo.client.post('/api/ask', json=dict(conv_id=cid, question=question, **options))
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['texte_en_attente'] is False
    assert not demo.appels
    return d


@pytest.mark.parametrize('fournisseur', ['gemini', 'openai', 'groq'])
def test_ancols_et_clients_moraux_sans_api(demo, fournisseur):
    cid = demo.client.post('/api/conversations').json()['id']
    naturel = envoyer(demo, cid, SCENARIO_1[0], fournisseur=fournisseur)
    assert naturel['reponse'] and naturel['resultats'] is None and naturel['sql_genere'] is None
    resultat = envoyer(demo, cid, SCENARIO_1[1], fournisseur=fournisseur)
    rows = resultat['resultats']['rows']
    assert len(rows) == len({r['ID_client'] for r in rows}) == 17
    with demo.S._connect_read_only() as c:
        attendus = {r[0] for r in c.execute("SELECT DISTINCT ID_client FROM Occupant WHERE Type_personne='Morale'")}
    assert {r['ID_client'] for r in rows} == attendus
    assert resultat['resultats']['fournisseur_sql'] == 'local'


def test_dpe_age_etage_contacts_carte_et_exports_sans_api(demo):
    cid = demo.client.post('/api/conversations').json()['id']
    resultats = []
    for i, q in enumerate(SCENARIO_2):
        # Recharger la conversation et vider le cache ne doit pas perdre les filtres.
        if i:
            assert demo.client.get('/api/conversations/' + cid).status_code == 200
            from boutique.chat import _sql_cache
            _sql_cache.clear()
        resultats.append(envoyer(demo, cid, q))
    assert [r['resultats']['row_count'] for r in resultats] == [23, 14, 8, 8]
    avant, fin = [r['resultats']['rows'] for r in resultats[-2:]]
    assert {(r['ID_occupant'], r['ID_lot']) for r in avant} == {(r['ID_occupant'], r['ID_lot']) for r in fin}
    with demo.S._connect_read_only() as c:
        for row in fin:
            assert row['Age_occupant'] > 65 and row['Etage'] >= 2
            assert c.execute('''SELECT COUNT(*) FROM Equipement e JOIN Patrimoine_lot_pivot pl
                ON e.ID_patrimoine_lot=pl.ID_patrimoine_lot WHERE pl.ID_lot=?
                AND e.Libelle_type_equipement='Ascenseur' AND e.Indicateur_activite='Oui' ''',
                (row['ID_lot'],)).fetchone()[0] == 0
            derniere = c.execute('SELECT MAX(date(Date_ouverture)) FROM Affaire WHERE ID_client_demandeur_affaire=?',
                                 (row['ID_client'],)).fetchone()[0]
            assert row['Derniere_ouverture_affaire'] == derniere
    dates = [r['Derniere_ouverture_affaire'] for r in fin if r['Derniere_ouverture_affaire']]
    assert dates == sorted(dates)
    assert all(r.get('Telephone_occupant') or r.get('Mail_occupant') for r in fin)
    final = resultats[-1]
    assert final['resultats']['localisation_demandee'] is True
    assert 'ouverture d’affaire' in final['reponse']
    carte = demo.client.get('/api/carte', params=dict(message_id=final['id']))
    assert carte.status_code == 200, carte.text
    assert {r['id'] for r in carte.json()['points']} == {r['ID_patrimoine'] for r in fin}
    assert not carte.json()['ignores'] and not carte.json()['tronque']
    for format in ('csv', 'json', 'pdf', 'xlsx'):
        export = demo.client.get('/api/export/' + str(final['id']), params=dict(format=format))
        assert export.status_code == 200, export.text
        assert export.content
    # Même la route de rédaction ne doit pas dépendre d'un fournisseur.
    assert demo.client.post('/api/ask/' + str(final['id']) + '/texte').json()['reponse'] == final['reponse']
    assert demo.S.q('SELECT COUNT(*) AS n FROM gemini_log', one=True)['n'] == 0


def test_selection_isolee_par_conversation_et_droits(demo):
    cid = demo.client.post('/api/conversations').json()['id']
    premier = envoyer(demo, cid, SCENARIO_2[0])
    autre = demo.client.post('/api/conversations').json()['id']
    clarification = envoyer(demo, autre, SCENARIO_2[1])
    assert clarification['resultats'] is None and clarification['sql_genere'] is None
    demo.S.q("UPDATE permissions SET columns=? WHERE service_id=? AND table_name='Occupant'",
             (json.dumps(['ID_occupant', 'ID_client']), demo.sid), write=True)
    refus = demo.client.post('/api/ask', json=dict(conv_id=cid, question=SCENARIO_2[1]))
    # Le changement des droits invalide le contexte précédent : aucune extraction.
    assert refus.status_code == 200 and refus.json()['resultats'] is None
    refus = demo.client.post('/api/ask', json=dict(conv_id=cid, question=SCENARIO_1[1]))
    assert refus.status_code == 403
    assert not demo.appels
    assert demo.client.get('/api/export/' + str(premier['id'])).status_code == 403


@pytest.mark.parametrize('question', [
    'Donne moi la liste des clients moraux à Rennes',
    'Les patrimoines avec un DPE F ou G à Nantes',
    'Les patrimoines avec un DPE F ou G sauf les résidences vendues',
    'Donne moi les personnes de moins de 65 ans qui vivent dans ces logements',
    "Parmi ces gens là donne moi dans l'ordre décroissant le dernier contact que l'on a eu avec eux",
])
def test_criteres_supplementaires_ne_sont_jamais_ignores(question):
    assert reconnaitre(question, {}) is None


@pytest.mark.parametrize('lettres', [["F'); DROP TABLE Client; --"], ['Z'], [], [None]])
def test_contexte_invalide_non_execute(lettres):
    r = reconnaitre(SCENARIO_2[1], {}, dict(version=1, lettres=lettres, cible='patrimoines'))
    assert r.reponse and not r.sql


def test_seuils_ascenseur_dates_absentes_et_doublons():
    with sqlite3.connect(':memory:') as c:
        c.row_factory = sqlite3.Row
        c.executescript('''
        CREATE TABLE Patrimoine(ID_patrimoine TEXT, Libelle_patrimoine TEXT, Libelle_commune TEXT);
        INSERT INTO Patrimoine VALUES('P1','Résidence test','Test');
        CREATE TABLE Lot(ID_lot TEXT,ID_patrimoine TEXT,Etage INTEGER);
        INSERT INTO Lot VALUES('L65','P1',2),('L66','P1',2),('L70','P1',2),('L80','P1',1),('L90','P1',3);
        CREATE TABLE Occupant(ID_occupant TEXT,ID_client TEXT,Nom_occupant TEXT,Prenom_occupant TEXT,
            Age_occupant INTEGER,Telephone_occupant TEXT,Mail_occupant TEXT);
        INSERT INTO Occupant VALUES('O65','C65','Test','65',65,NULL,NULL),('O66','C66','Test','66',66,'0600000000','test@example.invalid'),
            ('O70','C70','Test','70',70,NULL,NULL),('O80','C80','Test','80',80,NULL,NULL),('O90','C90','Test','90',90,NULL,NULL);
        CREATE TABLE Client_lot_pivot(ID_client TEXT,ID_lot TEXT);
        INSERT INTO Client_lot_pivot VALUES('C65','L65'),('C66','L66'),('C70','L70'),('C80','L80'),('C90','L90');
        CREATE TABLE Diagnostic(ID_diagnostic TEXT,ID_lot TEXT);
        INSERT INTO Diagnostic VALUES('D65','L65'),('D66','L66'),('D66bis','L66'),('D70','L70'),('D80','L80'),('D90','L90');
        CREATE TABLE Diagnostic_valeur(ID_diagnostic TEXT,Type_valeur TEXT,Valeur TEXT);
        INSERT INTO Diagnostic_valeur SELECT ID_diagnostic,'Lettre_DPE_EP','F' FROM Diagnostic;
        CREATE TABLE Equipement(ID_patrimoine_lot TEXT,Libelle_type_equipement TEXT,Indicateur_activite TEXT);
        INSERT INTO Equipement VALUES('PL66','Ascenseur','Non'),('PL70','Ascenseur','Oui');
        CREATE TABLE Patrimoine_lot_pivot(ID_patrimoine_lot TEXT,ID_lot TEXT);
        INSERT INTO Patrimoine_lot_pivot VALUES('PL66','L66'),('PL70','L70');
        CREATE TABLE Affaire(ID_client_demandeur_affaire TEXT,Date_ouverture TEXT);
        INSERT INTO Affaire VALUES('C66','2024-01-01'),('C66','2026-01-01'),('C90',NULL),('C90','2099-12-31');
        ''')
        schema = {r[0].lower(): {col[1].lower() for col in c.execute(f'PRAGMA table_info("{r[0]}")')}
                  for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        contexte = None
        for i, question in enumerate(SCENARIO_2):
            recherche = reconnaitre(question, schema, contexte)
            contexte = recherche.contexte
            rows = c.execute(recherche.sql).fetchall()
            if i == 1:
                assert {r['ID_occupant'] for r in rows} == {'O66','O70','O80','O90'}
                assert len(rows) == 4  # Deux diagnostics de L66 ne doublent pas la personne.
        assert [r['ID_occupant'] for r in rows] == ['O66','O90']
        assert [r['Derniere_ouverture_affaire'] for r in rows] == ['2026-01-01', None]


def test_bibliotheques_carte_embarquees(demo):
    import hashlib
    manifest = json.loads((ROOT / 'web/static/vendor/manifest.json').read_text(encoding='utf-8'))
    for chemin, meta in manifest.items():
        r = demo.client.get('/static/vendor/' + chemin)
        assert r.status_code == 200
        assert hashlib.sha256(r.content).hexdigest() == meta['sha256']
    carte = demo.client.get('/carte').text
    assert 'https://unpkg.com/' not in carte
