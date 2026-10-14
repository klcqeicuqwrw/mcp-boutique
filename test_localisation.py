import sqlite3

import pytest
from test_web import web, connecter
from boutique.localisation import demandee


@pytest.fixture
def geographie(web, monkeypatch):
    with sqlite3.connect(web.S.DATABASE_PATH) as c:
        c.executescript("""
        CREATE TABLE Lot(ID_lot TEXT, ID_patrimoine TEXT);
        INSERT INTO Lot VALUES('L1','P1'),('L2','P2');
        CREATE TABLE Client_lot_pivot(ID_client TEXT, ID_lot TEXT);
        INSERT INTO Client_lot_pivot VALUES('C1','L1'),('C2','L2');
        CREATE TABLE Occupant(ID_occupant TEXT, ID_client TEXT);
        INSERT INTO Occupant VALUES('O1','C1'),('O2','C2');
        UPDATE Patrimoine SET Latitude='47.2',Longitude='-1.5' WHERE ID_patrimoine='P2';
        """)
    for t in ('Lot','Client_lot_pivot','Occupant'):
        web.S.q('INSERT INTO permissions VALUES(?,?,NULL)',(web.sid,t),write=True)
    web.S._schema_cache.clear()
    monkeypatch.setattr(web.chat,'generer_sql',lambda *a,**kw:'SELECT ID_lot FROM Lot ORDER BY ID_lot')
    connecter(web)
    yield web


def question(web, texte):
    cid=web.client.post('/api/conversations').json()['id']
    r=web.client.post('/api/ask',json=dict(conv_id=cid,question=texte))
    assert r.status_code==200,r.text
    return cid,r.json()


def test_carte_uniquement_sur_demande_et_reprise_sans_ia(geographie,monkeypatch):
    web=geographie
    cid,r=question(web,'Liste les logements')
    assert r['resultats']['localisation_demandee'] is False
    monkeypatch.setattr(web.chat,'generer_sql',lambda *a,**kw:pytest.fail('La sélection existe déjà'))
    r=web.client.post('/api/ask',json=dict(conv_id=cid,question='Localise ces résultats'))
    assert r.status_code==200,r.text
    res=r.json()
    assert res['resultats']['localisation_demandee'] is True
    points=web.client.get('/api/carte?message_id='+str(res['id'])).json()['points']
    assert {p['id'] for p in points}=={'P1','P2'}


@pytest.mark.parametrize('identifiant,selection', [('ID_lot','L1'),('ID_client','C1'),('ID_occupant','O1')])
def test_resolution_des_identifiants(geographie,monkeypatch,identifiant,selection):
    web=geographie
    monkeypatch.setattr(web.chat,'generer_sql',lambda *a,**kw:f"SELECT '{selection}' AS {identifiant}")
    _,r=question(web,'Affiche ces logements sur une carte')
    assert r['resultats']['localisation_demandee'] is True
    carte=web.client.get('/api/carte?message_id='+str(r['id']))
    assert carte.status_code==200,carte.text
    assert [p['id'] for p in carte.json()['points']]==['P1']


def test_propriete_et_retrait_des_droits(geographie):
    web=geographie
    cid,r=question(web,'Affiche les logements sur la carte')
    web.S.q("DELETE FROM permissions WHERE service_id=? AND table_name='Lot'",(web.sid,),write=True)
    assert web.client.get('/api/carte?message_id='+str(r['id'])).status_code==403
    assert web.client.post('/api/ask',json=dict(conv_id=cid,question='Localise ces résultats')).status_code==403
    connecter(web,'bob')
    assert web.client.get('/api/carte?message_id='+str(r['id'])).status_code==404


def test_identifiants_parametres_sans_injection(geographie,monkeypatch):
    web=geographie
    monkeypatch.setattr(web.chat,'generer_sql',lambda *a,**kw:"SELECT 'x''); OR 1=1 --' AS ID_lot")
    _,r=question(web,'Localise les logements')
    carte=web.client.get('/api/carte?message_id='+str(r['id']))
    assert carte.status_code==200,carte.text
    assert carte.json()['points']==[]


@pytest.mark.parametrize('texte,attendu', [
    ('Liste les logements',False),('Affiche les logements sur une carte',True),
    ('Localise ces résultats',True),('Sans carte',False),('Ne localise pas les résultats',False),
    ('Clients payant par carte bancaire',False),('Où se trouvent ces logements ?',True),
    ('Ne les affiche pas sur une carte',False),
])
def test_intention_localisation(texte,attendu):
    assert demandee(texte) is attendu
