"""Outils collaborateurs : droits, relations, échéances et favoris isolés par compte."""
import json
import sqlite3
import pytest
from test_web import web, connecter


@pytest.fixture
def espace(web):
    with sqlite3.connect(web.S.DATABASE_PATH) as c:
        c.executescript('''
        CREATE TABLE Lot(ID_lot TEXT, ID_patrimoine TEXT, Code_lot TEXT, Code_societe TEXT);
        INSERT INTO Lot VALUES('L1','P1','1','AJ');
        CREATE TABLE Client_lot_pivot(ID_client_lot TEXT,ID_client TEXT,ID_lot TEXT);
        INSERT INTO Client_lot_pivot VALUES('CL1','C1','L1');
        CREATE TABLE Occupant(ID_occupant TEXT,ID_client TEXT,Mail_occupant TEXT,Nom_occupant TEXT);
        INSERT INTO Occupant VALUES('O1','C1','alice@example.invalid','SECRET_OCCUPANT');
        CREATE TABLE Bail(ID_bail TEXT,ID_client TEXT,ID_lot TEXT,Indicateur_occupation_active TEXT,Date_reception_preavis TEXT);
        INSERT INTO Bail VALUES('B1','C1','L1','Actif','2026-10-01'),('B2','C2','L1','Actif','2099-01-01'),('B3','C2','L1','Inactif','2026-09-01');
        CREATE TABLE Affaire(ID_Affaire TEXT,ID_client_demandeur_affaire TEXT,ID_lot TEXT,Indicateur_statut_etat_affaire TEXT,Date_theorique_cloture TEXT,Code_collaborateur_suivi TEXT);
        INSERT INTO Affaire VALUES('A1','C1','L1','Ouvert','2026-09-01','COL1'),('A2','C2','L1','Fermé','2026-09-01','COL1');
        ALTER TABLE Commande ADD COLUMN Taux_execution_commande REAL;
        ALTER TABLE Commande ADD COLUMN Date_fin_execution_commande TEXT;
        ALTER TABLE Commande ADD COLUMN Mail_tiers TEXT;
        ALTER TABLE Commande ADD COLUMN Code_collaborateur_executant_commande TEXT;
        UPDATE Commande SET Taux_execution_commande=50,Date_fin_execution_commande='2026-09-01',Mail_tiers='tiers@example.invalid',Code_collaborateur_executant_commande='COL1' WHERE ID_commande='CMD1';
        UPDATE Commande SET Taux_execution_commande=100,Date_fin_execution_commande='2026-09-01' WHERE ID_commande='CMD2';
        ALTER TABLE Intervention ADD COLUMN ID_lot TEXT;
        UPDATE Intervention SET ID_lot='L1';
        CREATE TABLE Collaborateur(Code_collaborateur TEXT,Nom_prenom_collaborateur TEXT,Mail_collaborateur TEXT);
        INSERT INTO Collaborateur VALUES('COL1','Responsable','responsable@example.invalid');
        CREATE TABLE Diagnostic(ID_diagnostic TEXT,ID_lot TEXT,Date_fin_diagnostic TEXT,Indicateur_diagnostic_le_plus_recent TEXT,Lien_URL_diagnostic TEXT,Date_actualisation TEXT);
        INSERT INTO Diagnostic VALUES('D1','L1','2026-11-01','Oui','https://example.invalid/doc','2025-01-01'),('D2','L1','2026-01-01','Non',NULL,'2025-01-01'),('D3','L1','2099-12-31','Oui',NULL,'2025-01-01');
        CREATE TABLE Diagnostic_valeur(ID_diagnostic TEXT,Type_valeur TEXT,Valeur TEXT);
        INSERT INTO Diagnostic_valeur VALUES('D1','DPE','F');
        CREATE TABLE Copropriete(ID_copropriete TEXT,ID_patrimoine TEXT,Etat_mandat_copropriete TEXT,Date_fin_mandat_copropriete TEXT);
        INSERT INTO Copropriete VALUES('CP1','P1','Mandat en cours','2026-11-01'),('CP2','P1','Pas de mandat en cours','2026-01-01');
        CREATE TABLE Releve_compte_client_historique(ID_client TEXT,Annee_mois TEXT,Montant_impaye REAL,Montant_loyer REAL);
        INSERT INTO Releve_compte_client_historique VALUES('C1','2026-08-01',100,500),('C1','2026-09-01',0,500),('C2','2026-09-01',50,600);
        ''')
    for t in ('Lot','Client_lot_pivot','Occupant','Bail','Affaire','Commande','Intervention','Collaborateur','Diagnostic','Diagnostic_valeur','Copropriete','Releve_compte_client_historique'):
        web.S.q('INSERT INTO permissions VALUES(?,?,NULL)', (web.sid,t), write=True)
    connecter(web)
    return web


def test_fiches_relations_et_historique(espace):
    c=espace.client
    r=c.get('/api/espace/fiche/client?identifiant=C1')
    assert r.status_code==200, r.text
    sections={s['table']:s['resultats'] for s in r.json()['sections']}
    assert sections['Lot']['rows'][0]['ID_lot']=='L1'
    assert sections['Occupant']['rows'][0]['ID_occupant']=='O1'
    assert sections['Releve_compte_client_historique']['rows'][0]['Annee_mois']=='2026-09-01'
    assert len(sections['Client']['rows'])==2  # Grain client × lot conservé.
    r=c.get('/api/espace/fiche/commande?identifiant=CMD1')
    assert r.status_code==200
    sections={s['table']:s['resultats'] for s in r.json()['sections']}
    assert len(sections['Intervention']['rows'])==2
    assert sections['Collaborateur']['rows'][0]['Mail_collaborateur']=='responsable@example.invalid'
    r=c.get('/api/espace/fiche/lot?identifiant=L1')
    assert r.status_code==200
    assert any(s['table']=='Patrimoine' for s in r.json()['sections'])


def test_fiche_colonnes_restreintes_et_relation_interdite(espace):
    s=espace.S
    s.q('UPDATE permissions SET columns=? WHERE service_id=? AND table_name=?', (json.dumps(['ID_client','ID_occupant']),espace.sid,'Occupant'),write=True)
    s.q('DELETE FROM permissions WHERE service_id=? AND table_name=?',(espace.sid,'Client_lot_pivot'),write=True)
    r=espace.client.get('/api/espace/fiche/client?identifiant=C1')
    assert r.status_code==200
    assert 'SECRET_OCCUPANT' not in r.text and 'alice@example.invalid' not in r.text
    assert not any(x['table']=='Lot' for x in r.json()['sections'])
    s.q('UPDATE permissions SET columns=? WHERE service_id=? AND table_name=?',(json.dumps(['Nom_prenom_client']),espace.sid,'Client'),write=True)
    assert espace.client.get('/api/espace/fiche/client?identifiant=C1').status_code==403


def test_identifiants_parametres_et_fiche_absente(espace):
    for ident in ['absent', "C1' OR 1=1 --"]:
        assert espace.client.get('/api/espace/fiche/client',params={'identifiant':ident}).status_code==404
    assert espace.client.get('/api/espace/fiche/inconnu?identifiant=C1').status_code==404


def test_a_traiter_regles_dates_et_dernier_mois(espace):
    r=espace.client.get('/api/espace/a-traiter?au=2026-10-14')
    assert r.status_code==200,r.text
    cartes={c['code']:c for c in r.json()['cartes']}
    assert all(c['disponible'] for c in cartes.values())
    assert {k:c['total'] for k,c in cartes.items()}==dict(affaires=1,commandes=1,diagnostics=1,departs=1,mandats=1,comptes=1)
    assert cartes['diagnostics']['actualisation']=='2025-01-01'
    r=espace.client.get('/api/espace/a-traiter?au=2026-10-14&categorie=comptes')
    assert [x['ID_client'] for x in r.json()['cartes'][0]['resultats']['rows']]==['C2']
    assert espace.client.get('/api/espace/a-traiter?au=incorrect').status_code==422
    assert espace.client.get('/api/espace/a-traiter?au=2026-10-14&categorie=inconnu').status_code==404


def test_a_traiter_ne_lit_pas_colonne_interdite(espace):
    espace.S.q('UPDATE permissions SET columns=? WHERE service_id=? AND table_name=?',(json.dumps(['ID_commande']),espace.sid,'Commande'),write=True)
    r=espace.client.get('/api/espace/a-traiter?au=2026-10-14&categorie=commandes')
    assert r.status_code==200
    assert r.json()['cartes'][0]['disponible'] is False
    assert 'total' not in r.json()['cartes'][0]


def test_comptes_exclut_mois_futurs_a_date_reference(espace):
    with sqlite3.connect(espace.S.DATABASE_PATH) as c:
        c.execute("INSERT INTO Releve_compte_client_historique VALUES('C1','2026-11-01',999,500)")
    r=espace.client.get('/api/espace/a-traiter?au=2026-10-14&categorie=comptes')
    assert r.status_code==200
    assert [x['ID_client'] for x in r.json()['cartes'][0]['resultats']['rows']]==['C2']


def test_carte_interne_selection_et_droits(espace):
    r=espace.client.get('/api/espace/itineraire/lot?identifiant=L1',follow_redirects=False)
    assert r.status_code==307,r.text
    assert r.headers['location']=='/carte?type_entite=lot&identifiant=L1'
    assert espace.client.get('/api/espace/carte/lot?identifiant=L1',follow_redirects=False).headers['location']==r.headers['location']
    r=espace.client.get('/api/carte?type_entite=lot&identifiant=L1')
    assert r.status_code==200,r.text
    assert [p['id'] for p in r.json()['points']]==['P1']
    assert r.json()['filtre'] is True
    espace.S.q('UPDATE permissions SET columns=? WHERE service_id=? AND table_name=?',(json.dumps(['ID_patrimoine']),espace.sid,'Patrimoine'),write=True)
    assert espace.client.get('/api/carte?type_entite=lot&identifiant=L1').status_code==403


@pytest.mark.parametrize('type_entite,identifiant', [('client','C1'),('occupant','O1'),('affaire','A1'),('commande','CMD1'),('diagnostic','D1'),('copropriete','CP1'),('patrimoine','P1')])
def test_carte_filtree_sur_chaque_type_fiche(espace,type_entite,identifiant):
    r=espace.client.get('/api/carte',params=dict(type_entite=type_entite,identifiant=identifiant))
    assert r.status_code==200,r.text
    assert [p['id'] for p in r.json()['points']]==['P1']
    assert 'SECRET' not in r.text


def test_carte_selection_invalide_coordonnees_et_injection(espace):
    c=espace.client
    assert c.get('/api/carte?type_entite=lot').status_code==400
    assert c.get('/api/carte?type_entite=inconnu&identifiant=L1').status_code==400
    assert c.get('/api/carte?latitude=50').status_code==400
    assert c.get('/api/carte?latitude=91&longitude=3').status_code==422
    assert c.get('/api/carte?type_entite=lot&identifiant=L1&latitude=50&longitude=3').status_code==400
    r=c.get('/api/carte?latitude=50.63&longitude=3.06')
    assert r.status_code==200
    assert [p['id'] for p in r.json()['points']]==['P1']
    r=c.get('/api/carte',params=dict(type_entite='lot',identifiant="L1' OR 1=1 --"))
    assert r.status_code==200 and r.json()['points']==[]
    espace.S.q('DELETE FROM permissions WHERE service_id=? AND table_name=?',(espace.sid,'Client_lot_pivot'),write=True)
    assert c.get('/api/carte?type_entite=client&identifiant=C1').status_code==403


def test_favoris_persistants_isoles_et_validation(espace):
    c=espace.client
    p=dict(label=' Mes retards ',question=' Affaires en retard ')
    assert c.post('/api/espace/favoris',json=p).status_code==200
    assert c.post('/api/espace/favoris',json=p).status_code==200
    favoris=c.get('/api/espace/favoris').json()
    assert len(favoris)==1 and favoris[0]['label']=='Mes retards'
    fid=favoris[0]['id']
    connecter(espace,'bob')
    assert c.get('/api/espace/favoris').json()==[]
    assert c.delete(f'/api/espace/favoris/{fid}').status_code==404
    connecter(espace)
    assert c.post('/api/espace/favoris',json=dict(label=' ',question='x')).status_code==422
    assert c.delete(f'/api/espace/favoris/{fid}').status_code==200
    assert c.get('/api/espace/favoris').json()==[]


def test_espace_authentification_csrf_et_changement_droits(espace,monkeypatch):
    c=espace.client
    c.headers.pop('X-Requested-With')
    assert c.post('/api/espace/favoris',json=dict(label='x',question='x')).status_code==403
    c.headers['X-Requested-With']='fetch'
    monkeypatch.setattr(espace.S,'scope_actuel',lambda *a:False)
    assert c.get('/api/espace/fiche/client?identifiant=C1').status_code==403
    assert c.get('/api/espace/a-traiter?au=2026-10-14').status_code==403
    c.cookies.clear()
    for url in ['/api/espace/favoris','/api/espace/fiche/client?identifiant=C1','/api/espace/a-traiter?au=2026-10-14','/api/espace/itineraire/lot?identifiant=L1']:
        assert c.get(url,follow_redirects=False).status_code==401
