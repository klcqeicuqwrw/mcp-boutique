"""Enrichissement reproductible : test dans une copie en mémoire, jamais sur le DWH."""
from pathlib import Path
import sqlite3
from scripts.enrichir_historiques_predictions import enrichir, ORIGINE


def test_enrichissement_preserve_sources_et_equilibres_et_est_idempotent():
    origine=Path(__file__).parent/'DWH_fictive_10000_lignes.sqlite'
    c=sqlite3.connect(':memory:')
    c.row_factory=sqlite3.Row
    with sqlite3.connect(origine.resolve().as_uri()+'?mode=ro',uri=True) as source:
        source.backup(c)
    tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in ['Releve_compte_client_historique','Intervention','Commande']:
        colonnes={r[1] for r in c.execute(f'PRAGMA table_info("{table}")')}
        if 'Origine_donnees' in colonnes:
            c.execute(f'DELETE FROM "{table}" WHERE Origine_donnees=?',(ORIGINE,))
    if 'Simulation_dataset' in tables:
        c.execute('DELETE FROM Simulation_dataset WHERE ID_simulation=?',('predictions-v1',))
    colonnes={r[1] for r in c.execute('PRAGMA table_info(Equipement)')}
    if 'Origine_observation' in colonnes:
        c.execute('UPDATE Equipement SET Date_debut_observation=NULL,Date_fin_observation=NULL,Origine_observation=NULL WHERE Origine_observation=?',(ORIGINE,))
    anciens=[tuple(r) for r in c.execute('SELECT ID_client,Annee_mois,Montant_impaye FROM Releve_compte_client_historique ORDER BY 1,2')]
    resultat=enrichir(c)
    assert resultat['comptes_ajoutes']>0 and resultat['pannes_ajoutees']>0
    apres={(r['ID_client'],r['Annee_mois']):r['Montant_impaye'] for r in c.execute('SELECT ID_client,Annee_mois,Montant_impaye FROM Releve_compte_client_historique')}
    assert all(apres[(ident,m)]==val for ident,m,val in anciens)
    assert c.execute('SELECT COUNT(DISTINCT Annee_mois) FROM Releve_compte_client_historique').fetchone()[0]>=21
    incoherents=c.execute('''SELECT COUNT(*) FROM Releve_compte_client_historique a
        JOIN Releve_compte_client_historique b ON b.ID_client=a.ID_client AND b.Annee_mois=date(a.Annee_mois,'-1 month')
        WHERE a.Origine_donnees=? AND ABS(a.Montant_impaye-MAX(0,b.Montant_impaye+a.Montant_loyer+a.Montant_charges-a.Montant_APL-a.Montant_RLS-a.Montant_paiement_moins_remboursement))>0.00001''',(ORIGINE,)).fetchone()[0]
    assert incoherents==0
    incoherents=c.execute('''SELECT COUNT(*) FROM Intervention i LEFT JOIN Equipement e ON e.ID_equipement=i.ID_equipement
        LEFT JOIN Commande cmd ON cmd.ID_commande=i.ID_commande WHERE i.Origine_donnees=? AND
        (e.ID_equipement IS NULL OR cmd.ID_commande IS NULL OR i.Date_realisation_intervention<e.Date_debut_observation
        OR i.Date_realisation_intervention>e.Date_fin_observation)''',(ORIGINE,)).fetchone()[0]
    assert incoherents==0
    compte=c.execute('SELECT COUNT(*) FROM Releve_compte_client_historique').fetchone()[0]
    pannes=c.execute('SELECT COUNT(*) FROM Intervention').fetchone()[0]
    second=enrichir(c)
    assert second['deja_genere'] is True
    assert second['comptes_ajoutes']==0 and second['pannes_ajoutees']==0
    assert c.execute('SELECT COUNT(*) FROM Releve_compte_client_historique').fetchone()[0]==compte
    assert c.execute('SELECT COUNT(*) FROM Intervention').fetchone()[0]==pannes
    c.close()
