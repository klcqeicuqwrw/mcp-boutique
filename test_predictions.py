"""Prévisions : chronologie, qualité des labels, calculs ML et permissions."""
from copy import deepcopy
from datetime import date, timedelta
import json
import math
import sqlite3

import pytest
from test_web import web, connecter
from boutique.apprentissage import Ridge, Logistique, Preparation, aire_roc
from boutique.predictions import projection_impayes, indice_equipements, signaux_equipements, signaux_directs


def comptes():
    rows=[]
    for mois,n in [(1,40),(2,40),(3,10)]:
        for i in range(n):
            rows.append(dict(ID_client=f'C-{i:02}',Annee_mois=f'2025-{mois:02}-01',
                             Montant_impaye=20+i*5+(mois-1)*15,Montant_loyer=450+i))
    return rows


def maintenance():
    equipements=[dict(ID_equipement=f'E-{i:02}',Code_societe='AJ',Code_lot=str(i),
        Libelle_type_equipement='Ascenseur',Date_mise_en_service='2018-01-01',Indicateur_activite='Oui') for i in range(20)]
    equipements.append(dict(ID_equipement='VMC',Code_societe='AJ',Code_lot='VMC',
        Libelle_type_equipement='VMC',Date_mise_en_service='2018-01-01'))
    lots=[dict(ID_lot='L-'+e['Code_lot'],Code_societe='AJ',Code_lot=e['Code_lot']) for e in equipements]
    interventions=[dict(ID_intervention=f'I-{i:02}',ID_lot='L-'+str(i),Code_intervention='ASC',
        Date_realisation_intervention=(date(2025,1,5)+timedelta(days=10*i)).isoformat(),
        objet='Cellule ascenseur HS') for i in range(20)]
    interventions.append(dict(ID_intervention='controle',ID_lot='L-0',Code_intervention='ASC',
                              Date_realisation_intervention='2026-09-22',objet='Controle ascenseur'))
    return equipements,lots,interventions


def test_ridge_relation_lineaire_et_imputation_apprise_sur_train():
    x=[[float(i),None] for i in range(100)]
    m=Ridge(alpha=.01).fit(x,[3*i+2 for i in range(100)])
    assert abs(m.predict([[101,None]])[0]-305)<.1
    p=Preparation()
    p.fit([[1,None],[3,4],[None,6]])
    avant=(list(p.medianes),list(p.moyennes))
    p.transform([[1000000,1000000]])
    assert (p.medianes,p.moyennes)==avant


def test_logistique_et_auc_sur_exemples_connus():
    m=Logistique().fit([[i] for i in range(-20,21)],[int(i>=0) for i in range(-20,21)])
    assert m.converge
    assert m.predict_proba([[-15]])[0][1]<.1
    assert m.predict_proba([[15]])[0][1]>.9
    assert aire_roc([0,0,1,1],[.1,.4,.35,.8])==.75
    assert aire_roc([0,1],[.5,.5])==.5
    with pytest.raises(ValueError):
        aire_roc([0,0],[1,2])


def test_projection_cohorte_fixe_et_mois_partiel():
    p=projection_impayes(comptes(),date(2026,10,15),['Montant_impaye','Montant_loyer'])
    assert p['disponible']
    assert p['clients']==40 and p['transitions_apprentissage']==40
    assert p['mois_base']=='2025-02-01' and p['mois_projection']=='2025-03-01'
    assert p['projection_historique'] is True
    assert p['validation']['observations']==10
    assert p['validation']['ameliore_reference'] is True
    assert p['audit']['couverture_mensuelle'][-1]['retenu'] is False
    assert len(p['historique'])==2 and p['montant_prevu']>=0
    assert 'C-00' not in json.dumps(p)


def test_aucune_cible_future_dans_apprentissage():
    lignes=comptes()
    avant=projection_impayes(lignes,date(2026,10,15),['Montant_impaye'])
    apres=deepcopy(lignes)
    for r in apres:
        if r['Annee_mois']=='2025-03-01':
            r['Montant_impaye']=999999
    apres=projection_impayes(apres,date(2026,10,15),['Montant_impaye'])
    assert avant['montant_prevu']==apres['montant_prevu']
    assert avant['derniere_cible_apprentissage']=='2025-02-01'
    assert avant['validation']['erreur_moyenne_euros']!=apres['validation']['erreur_moyenne_euros']
    futur=lignes+[dict(ID_client='FUTUR',Annee_mois='2027-01-01',Montant_impaye=999999)]
    assert projection_impayes(futur,date(2026,10,15),['Montant_impaye'])==avant


def test_valeurs_invalides_doublons_et_historique_insuffisant():
    lignes=comptes()
    original=projection_impayes(lignes,date(2026,10,15),['Montant_impaye'])
    assert projection_impayes(lignes+[lignes[0]],date(2026,10,15),['Montant_impaye'])==original
    conflit=dict(lignes[0],Montant_impaye=999)
    p=projection_impayes(lignes+[conflit],date(2026,10,15),['Montant_impaye'])
    assert p['clients']==39 and p['audit']['client_mois_contradictoires']==1
    invalide=dict(lignes[0],Montant_impaye=float('inf'))
    p=projection_impayes(lignes+[invalide],date(2026,10,15),['Montant_impaye'])
    assert p['audit']['lignes_invalides']==1
    assert projection_impayes(lignes[:40],date(2026,10,15),['Montant_impaye'])['disponible'] is False


def test_maintenance_label_indirect_et_pas_de_fausse_probabilite():
    e,l,i=maintenance()
    p=indice_equipements(e,l,i,date(2026,10,15))
    assert p['disponible'],p
    assert p['audit']['signaux_rapproches']==20
    assert p['equipements_estimables']==20 and p['equipements_non_estimables']==1
    assert p['validation']['disponible'] is False
    assert p['validation']['signaux_positifs']==0
    assert all(0<=r['Indice_priorite']<=100 for r in p['resultats']['rows'])
    assert all(math.isfinite(r['Indice_priorite']) for r in p['resultats']['rows'])
    assert not any('probabilite' in c.lower() for c in p['resultats']['columns'])


def test_controles_et_desaccords_de_type_ne_sont_pas_des_pannes():
    e,l,i=maintenance()
    controle=dict(i[0],ID_intervention='controle2',objet='Controle ascenseur')
    mauvais_type=dict(i[0],ID_intervention='mauvais-type',Code_intervention='VMC',ID_lot='L-VMC')
    sans_panne=dict(i[0],ID_intervention='sans-panne',objet='Controle ascenseur sans panne')
    _,_,_,audit=signaux_equipements(e,l,i+[controle,mauvais_type,sans_panne],date(2026,10,15))
    assert audit['signaux_rapproches']==20
    i=[dict(r,objet='Controle ascenseur') for r in i]
    assert indice_equipements(e,l,i,date(2026,10,15))['disponible'] is False


def test_rapprochement_ambigu_et_equipement_contradictoire_exclus():
    e,l,i=maintenance()
    duplique=dict(e[0],ID_equipement='E-autre')
    _,_,_,audit=signaux_equipements(e+[duplique],l,i,date(2026,10,15))
    assert audit['rapprochements_ambigus']==1 and audit['signaux_rapproches']==19
    contradictoire=dict(e[0],Code_lot='1')
    _,_,_,audit=signaux_equipements(e+[contradictoire],l,i,date(2026,10,15))
    assert audit['equipements_contradictoires']==1 and audit['signaux_rapproches']==19


def suivi_direct():
    e,l,i=maintenance()
    for r in e:
        r.update(Date_debut_observation='2024-01-01',Date_fin_observation='2026-09-30',Origine_observation='Simulation test')
    evenements=[dict(ID_intervention=r['ID_intervention'],ID_equipement='E-'+r['ID_intervention'][2:],
                     Indicateur_panne='Oui',Date_realisation_intervention=r['Date_realisation_intervention'])
                for r in i if r['ID_intervention'].startswith('I-')]
    return e,l,evenements


def test_pannes_directes_sans_rapprochement_et_date_de_suivi():
    e,l,i=suivi_direct()
    e.append(dict(e[0],ID_equipement='AUTRE-EQUIPEMENT-MEME-LOT'))
    p=indice_equipements(e,l,i,date(2026,10,15),directs=True)
    assert p['disponible'],p
    assert p['mode_labels']=='directs'
    assert p['date_reference_modele']=='2026-09-30'
    assert p['audit']['signaux_rapproches']==20
    assert p['audit']['rapprochements_ambigus']==0


def test_pas_de_panne_future_ou_hors_couverture_dans_suivi_direct():
    e,l,i=suivi_direct()
    i += [dict(i[0],ID_intervention='FUTUR',Date_realisation_intervention='2027-01-01'),
          dict(i[0],ID_intervention='HORS-SUIVI',Date_realisation_intervention='2026-10-01'),
          dict(i[0],ID_intervention='CONTROLE',Indicateur_panne='Non')]
    _,s,_,audit=signaux_directs(e,l,i,date(2026,10,15))
    assert sum(map(len,s.values()))==20
    assert audit['pannes_exclues']==1  # L'événement futur est ignoré, pas utilisé.
    for r in e:
        r.update(Date_debut_observation='2026-09-01',Date_fin_observation='2026-09-30')
    p=indice_equipements(e,l,i,date(2026,10,15),directs=True)
    assert p['disponible'] is False


@pytest.fixture
def prediction_web(web):
    with sqlite3.connect(web.S.DATABASE_PATH) as c:
        c.executescript('''
        CREATE TABLE Releve_compte_client_historique(ID_client TEXT,Annee_mois TEXT,Montant_impaye REAL,Montant_loyer REAL);
        CREATE TABLE Equipement(ID_equipement TEXT,Code_societe TEXT,Code_lot TEXT,Libelle_type_equipement TEXT,Date_mise_en_service TEXT);
        CREATE TABLE Lot(ID_lot TEXT,Code_societe TEXT,Code_lot TEXT);
        ALTER TABLE Commande ADD COLUMN Libelle_objet_commande_1 TEXT;
        ALTER TABLE Intervention ADD COLUMN ID_lot TEXT;
        ALTER TABLE Intervention ADD COLUMN Code_intervention TEXT;
        ALTER TABLE Intervention ADD COLUMN Date_realisation_intervention TEXT;
        ''')
        c.executemany('INSERT INTO Releve_compte_client_historique VALUES(?,?,?,?)',
            [(r['ID_client'],r['Annee_mois'],r['Montant_impaye'],r['Montant_loyer']) for r in comptes()])
        es,lots,interventions=maintenance()
        c.executemany('INSERT INTO Equipement VALUES(?,?,?,?,?)',[(r['ID_equipement'],r['Code_societe'],r['Code_lot'],r['Libelle_type_equipement'],r['Date_mise_en_service']) for r in es])
        c.executemany('INSERT INTO Lot VALUES(?,?,?)',[(r['ID_lot'],r['Code_societe'],r['Code_lot']) for r in lots])
        for r in interventions:
            c.execute('INSERT INTO Commande(ID_commande,Libelle_objet_commande_1) VALUES(?,?)',('CMD-'+r['ID_intervention'],r['objet']))
            c.execute('INSERT INTO Intervention VALUES(?,?,?,?,?)',(r['ID_intervention'],'CMD-'+r['ID_intervention'],r['ID_lot'],r['Code_intervention'],r['Date_realisation_intervention']))
    for t in ['Releve_compte_client_historique','Equipement','Lot','Intervention','Commande']:
        web.S.q('INSERT INTO permissions VALUES(?,?,NULL)',(web.sid,t),write=True)
    connecter(web)
    return web


def test_api_predictions_et_colonnes_restreintes(prediction_web):
    w=prediction_web
    r=w.client.get('/api/espace/predictions?au=2026-10-15')
    assert r.status_code==200,r.text
    assert r.json()['impayes']['disponible'] and r.json()['equipements']['disponible']
    assert 'C-00' not in r.text
    w.S.q('UPDATE permissions SET columns=? WHERE service_id=? AND table_name=?',
          (json.dumps(['ID_client','Annee_mois','Montant_impaye']),w.sid,'Releve_compte_client_historique'),write=True)
    r=w.client.get('/api/espace/predictions?au=2026-10-15')
    assert r.status_code==200 and r.json()['impayes']['variables']==['Montant_impaye']
    w.S.q('DELETE FROM permissions WHERE service_id=? AND table_name=?',(w.sid,'Commande'),write=True)
    r=w.client.get('/api/espace/predictions?au=2026-10-15')
    assert r.status_code==200 and r.json()['equipements']['disponible'] is False
    assert 'audit' not in r.json()['equipements']


def test_api_authentification_dates_et_retrait_droits(prediction_web,monkeypatch):
    w=prediction_web
    assert w.client.get('/api/espace/predictions').status_code==422
    assert w.client.get('/api/espace/predictions?au=incorrect').status_code==422
    monkeypatch.setattr(w.S,'scope_actuel',lambda *a:False)
    assert w.client.get('/api/espace/predictions?au=2026-10-15').status_code==403
    w.client.cookies.clear()
    assert w.client.get('/api/espace/predictions?au=2026-10-15').status_code==401


def test_api_suivi_direct_et_droits_specifiques(prediction_web):
    w=prediction_web
    with sqlite3.connect(w.S.DATABASE_PATH) as c:
        for col in ['Date_debut_observation','Date_fin_observation','Origine_observation']:
            c.execute(f'ALTER TABLE Equipement ADD COLUMN {col} TEXT')
        c.execute("UPDATE Equipement SET Date_debut_observation='2024-01-01',Date_fin_observation='2026-09-30',Origine_observation='Simulation test'")
        c.execute('ALTER TABLE Intervention ADD COLUMN ID_equipement TEXT')
        c.execute('ALTER TABLE Intervention ADD COLUMN Indicateur_panne TEXT')
        c.execute("UPDATE Intervention SET ID_equipement='E-'||substr(ID_intervention,3),Indicateur_panne='Oui' WHERE ID_intervention LIKE 'I-%'")
    w.S.q('DELETE FROM permissions WHERE service_id=? AND table_name=?',(w.sid,'Commande'),write=True)
    r=w.client.get('/api/espace/predictions?au=2026-10-15')
    assert r.status_code==200,r.text
    assert r.json()['equipements']['disponible'] and r.json()['equipements']['mode_labels']=='directs'
    cols=['ID_equipement','Code_societe','Code_lot','Libelle_type_equipement','Date_mise_en_service']
    w.S.q('UPDATE permissions SET columns=? WHERE service_id=? AND table_name=?',(json.dumps(cols),w.sid,'Equipement'),write=True)
    r=w.client.get('/api/espace/predictions?au=2026-10-15')
    assert r.status_code==200 and r.json()['equipements']['disponible'] is False
    assert 'audit' not in r.json()['equipements']
