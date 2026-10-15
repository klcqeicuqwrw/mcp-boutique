"""Complète la base FICTIVE pour la démonstration ML, sans remplacer les lignes.

Graine fixe, impayés janvier 2025–septembre 2026 et suivi équipements
octobre 2023–septembre 2026. Les pannes sont simulées et explicitement étiquetées.
Ne pas utiliser ce générateur sur des données de production.
"""
import argparse
import calendar
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import random
import re
import shutil
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
ORIGINE = 'Simulation predictions v1 — graine 20261015'
DEBUT_COMPTES = date(2025,1,1)
DEBUT_EQUIPEMENTS = date(2023,10,1)
FIN = date(2026,9,30)


def mois(debut, fin):
    m=debut.replace(day=1)
    while m<=fin:
        yield m
        m=date(m.year+(m.month==12),1 if m.month==12 else m.month+1,1)


def fin_mois(m):
    return m.replace(day=calendar.monthrange(m.year,m.month)[1])


def jour(v):
    try:
        return date.fromisoformat(str(v)[:10])
    except (ValueError,TypeError):
        return None


def inserer(c,table,donnees):
    cols=list(donnees)
    c.execute(f'INSERT INTO "{table}" ({",".join(chr(34)+k+chr(34) for k in cols)}) VALUES ({",".join("?" for _ in cols)})',tuple(donnees.values()))


def ajouter_colonnes(c,table,colonnes):
    connues={r[1] for r in c.execute(f'PRAGMA table_info("{table}")')}
    for col in colonnes:
        if col not in connues:
            c.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" TEXT')


def enrichir(c):
    for table,colonnes in {
        'Releve_compte_client_historique':['Origine_donnees'],
        'Commande':['Origine_donnees'],
        'Intervention':['ID_equipement','Indicateur_panne','Origine_donnees'],
        'Equipement':['Date_debut_observation','Date_fin_observation','Origine_observation'],
    }.items():
        ajouter_colonnes(c,table,colonnes)
    c.execute('CREATE TABLE IF NOT EXISTS Simulation_dataset (ID_simulation TEXT PRIMARY KEY, '
              'Origine_donnees TEXT NOT NULL, Parametres TEXT NOT NULL, Date_generation TEXT NOT NULL)')
    deja=c.execute('SELECT Origine_donnees FROM Simulation_dataset WHERE ID_simulation=?',('predictions-v1',)).fetchone()
    if deja:
        if deja[0]!=ORIGINE:
            raise ValueError('Une autre simulation utilise cet identifiant.')
        return dict(deja_genere=True,comptes_ajoutes=0,pannes_ajoutees=0,equipements_suivis=0)
    originaux=c.execute('SELECT * FROM Releve_compte_client_historique ORDER BY ID_client,Annee_mois').fetchall()
    par_client={}
    for r in originaux:
        par_client.setdefault(r['ID_client'],{})[r['Annee_mois']]=dict(r)
    if not par_client:
        raise ValueError('Aucun historique financier à prolonger.')
    occupations={r['ID_client']:jour(r['fin']) for r in c.execute('SELECT ID_client,MAX(Date_fin_occupation) AS fin FROM Client GROUP BY ID_client')}
    comptes_ajoutes=0
    for idx,(ident,historique) in enumerate(sorted(par_client.items())):
        rng=random.Random(f'20261015:compte:{ident}')
        original=historique[sorted(historique)[-1]]
        loyer_base=float(original.get('Montant_loyer') or 500)
        charges_base=float(original.get('Montant_charges') or 70)
        apl_base=min(loyer_base,float(original.get('Montant_APL') or 0))
        rls_base=min(max(0,loyer_base-apl_base),float(original.get('Montant_RLS') or 0))
        fragilite=rng.uniform(.03,.25)
        capacite_reglement=rng.uniform(.08,.35)
        impaye=0.0
        precedent=None
        for m in mois(DEBUT_COMPTES,FIN):
            cle=m.isoformat()
            if cle in historique:
                precedent=historique[cle]
                impaye=float(precedent.get('Montant_impaye') or 0)
                continue
            actif=not occupations.get(ident) or m<=occupations[ident]
            loyer=round(loyer_base*(1+.02*(m.year-2025))) if actif else 0
            charges=max(0,round(charges_base+rng.gauss(0,5))) if actif else 0
            apl=min(loyer,round(apl_base)) if actif else 0
            rls=min(max(0,loyer-apl),round(rls_base)) if actif else 0
            du=max(0,loyer+charges-apl-rls)
            ancien=impaye
            incident=rng.random()<fragilite+(0.04 if m.month in (1,9,12) else 0)
            manque=round(du*rng.uniform(.15,.85)) if incident else 0
            remboursement=round(min(ancien,ancien*capacite_reglement+rng.uniform(0,35))) if not incident else 0
            paiement=max(0,round(du-manque+remboursement+rng.gauss(0,12)))
            impaye=round(max(0,ancien+du-paiement),2)
            rejet=manque if incident and rng.random()<.6 else 0
            delta=round(impaye-ancien)
            fin=fin_mois(m).isoformat()
            societe=original.get('Code_societe') or ident.split('-')[0]
            code=original.get('Code_client') or ident.split('-')[-1]
            values=dict(ID_client=ident,ID_client_annee_mois=f'{ident}-{m:%Y-%m}',Annee_mois=cle,Annee_mois_ordre=cle,
                Code_societe=societe,Code_client=code,Montant_solde_client=impaye,
                Date_ecriture_retenue_solde_client=fin,Numero_ecriture_retenue_solde_client=1000000+(m.year-2025)*100000+m.month*1000+idx,
                Montant_impaye_potentiel=impaye,Montant_impaye_retardataire=impaye,Montant_impaye=impaye,
                Classe_montant_impaye='Pas de dette' if impaye==0 else 'Moins de 500 euros' if impaye<500 else '500 euros et plus',
                Classe_montant_impaye_potentiel='Pas de dette' if impaye==0 else 'Dette simulée',
                Montant_sommes_attente=0,Indicateur_anciennete_impaye='Oui' if ancien>0 and impaye>0 else 'Non',
                Indicateur_evolution_impaye='Hausse' if delta>0 else 'Baisse' if delta<0 else 'Stable',Evolution_montant_impaye=delta,
                Montant_loyer=loyer,Montant_loyer_residuel_hors_rappel_APL_RLS=max(0,loyer-apl-rls),
                Montant_loyer_residuel_avec_rappel_APL_RLS=max(0,loyer-apl-rls),Montant_APL=apl,Indicateur_APL='Oui' if apl else 'Non',
                Montant_rappel_APL=0,Montant_RLS=rls,Montant_rappel_RLS=0,Montant_allocation_logement=0,
                Montant_charges=charges,Montant_charges_facturation_client=charges,Montant_charges_facturation_immediate=0,
                Montant_SLS=0,Montant_penalite_SLS=0,Indicateur_penalite_SLS='Non',Montant_penalite_assurance=0,
                Indicateur_mandat_prelevement_quittancement='Oui',Jour_mandat_prelevement_quittancement=5,
                Libelle_type_paiement_majoritaire='Prélèvement',Montant_paiement_prelevement=paiement,Montant_rejet_prelevement=rejet,
                Montant_paiement_virement_bancaire=0,Montant_remboursement_virement_bancaire=0,Montant_paiement_carte_bancaire=0,
                Montant_paiement_cheque=0,Montant_remboursement_cheque=0,Montant_paiement_espece=0,Montant_paiement_mandat=0,
                Montant_paiement_tpe=0,Montant_paiement_ecriture_manuelle=0,Montant_paiement_moins_remboursement=paiement,
                Date_actualisation=fin+' 23:59:59.000',Origine_donnees=ORIGINE)
            inserer(c,'Releve_compte_client_historique',values)
            comptes_ajoutes+=1
            precedent=values
    lots={}
    for r in c.execute('SELECT ID_lot,Code_societe,Code_lot FROM Lot'):
        lots.setdefault((r['Code_societe'],r['Code_lot']),set()).add(r['ID_lot'])
    pannes_ajoutees,equipements_suivis=0,0
    for e in c.execute('SELECT * FROM Equipement ORDER BY ID_equipement').fetchall():
        if e['Origine_observation'] and e['Origine_observation']!=ORIGINE:
            continue
        installation=jour(e['Date_mise_en_service'])
        fin_service=jour(e['Date_fin_de_service']) or FIN
        debut=max(DEBUT_EQUIPEMENTS,installation) if installation else None
        fin=min(FIN,fin_service)
        candidates=lots.get((e['Code_societe'],e['Code_lot']),set())
        if not debut or debut>=fin or len(candidates)!=1:
            continue
        ident=e['ID_equipement']
        rng=random.Random(f'20261015:equipement:{ident}')
        vulnerabilite=rng.uniform(.6,1.5)
        dernier=None
        for m in mois(debut,fin):
            d=max(m,debut)
            age=(d-installation).days/365.25
            type_eq=e['Libelle_type_equipement']
            base={'Ascenseur':.025,'Chaudiere':.024,'VMC':.018,'Tableau electrique':.012,'Porte':.015}.get(type_eq,.018)
            saison=1.4 if type_eq=='Chaudiere' and m.month in (10,11,12,1,2,3) else 1.0
            recurrence=1.5 if dernier and (d-dernier).days<180 else 1.0
            probabilite=min(.25,(base+.003*max(0,age-5))*saison*vulnerabilite*recurrence)
            if rng.random()>=probabilite:
                continue
            borne=min(fin,fin_mois(m))
            panne=d+timedelta(days=rng.randrange((borne-d).days+1))
            remise=panne+timedelta(days=rng.randint(1,5))
            # Aucun retour en service fictif au-delà de la fin de suivi.
            realise=remise<=fin
            digest=hashlib.sha256(f'{ident}:{m:%Y-%m}'.encode()).hexdigest()[:18]
            cmd,intv='SIM-CMD-'+digest,'SIM-INT-'+digest
            lot=next(iter(candidates))
            cout=round(rng.uniform(80,800)*(1.6 if type_eq=='Ascenseur' else 1),2)
            code_inter={'Ascenseur':'ASC','VMC':'VMC','Tableau electrique':'ELE','Chaudiere':'CHF','Porte':'MEN'}.get(type_eq,'AUT')
            inserer(c,'Commande',dict(ID_commande=cmd,Code_societe=e['Code_societe'],Numero_commande='SIM-'+digest,Code_lot=e['Code_lot'],
                Type_commande='SIM',Libelle_type_commande='Maintenance corrective simulée',Libelle_objet_commande_1=f'Panne {type_eq} — simulation',
                Commentaire_commande=f'Exemple fictif lié à {ident}.',Montant_HT=cout,Montant_TVA=round(cout*.2,2),Montant_TTC=round(cout*1.2,2),
                Date_enregistrement_commande=panne.isoformat(),Date_signature_commande=panne.isoformat(),
                Date_debut_execution_commande=panne.isoformat(),Date_fin_execution_commande=remise.isoformat(),
                Taux_execution_commande=100 if realise else 0,Libelle_etat_commande='Soldée' if realise else 'En cours',
                Statut_commande='TRX' if realise else 'ENR',Libelle_statut_commande='Exécutée' if realise else 'Enregistrée',
                Date_actualisation=(remise if realise else panne).isoformat()+' 12:00:00.000',Origine_donnees=ORIGINE))
            inserer(c,'Intervention',dict(ID_intervention=intv,ID_commande=cmd,ID_lot=lot,ID_equipement=ident,Indicateur_panne='Oui',
                Code_lot_intervention=e['Code_lot'],Code_intervention=code_inter,Libelle_intervention=f'Panne {type_eq} simulée',
                Date_realisation_intervention=panne.isoformat(),Date_enregistrement_commande=panne.isoformat(),
                Quantite=1,Unite='unité',Prix_unitaire_HT=cout,Montant_total_HT=cout,Prix_unitaire_TVA=.2,Montant_total_TTC=round(cout*1.2,2),
                Livrable_attendu='Compte rendu simulé',Date_realisation_livrable=remise.isoformat() if realise else None,
                Indicateur_livrable_valide='Oui' if realise else 'Non',Date_actualisation=(remise if realise else panne).isoformat()+' 12:00:00.000',Origine_donnees=ORIGINE))
            dernier=panne
            pannes_ajoutees+=1
        c.execute('UPDATE Equipement SET Date_debut_observation=?,Date_fin_observation=?,Origine_observation=? WHERE ID_equipement=?',
                  (debut.isoformat(),fin.isoformat(),ORIGINE,ident))
        equipements_suivis+=1
    parametres=json.dumps(dict(graine=20261015,debut_comptes=str(DEBUT_COMPTES),debut_suivi=str(DEBUT_EQUIPEMENTS),fin=str(FIN),
        comptes_ajoutes=comptes_ajoutes,pannes_ajoutees=pannes_ajoutees,equipements_suivis=equipements_suivis),ensure_ascii=False)
    c.execute('INSERT INTO Simulation_dataset VALUES(?,?,?,?)',('predictions-v1',ORIGINE,parametres,datetime.now().isoformat(timespec='seconds')))
    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert c.execute('SELECT COUNT(*) FROM (SELECT ID_client,Annee_mois FROM Releve_compte_client_historique GROUP BY 1,2 HAVING COUNT(*)>1)').fetchone()[0]==0
    assert c.execute('SELECT COUNT(*) FROM Intervention i LEFT JOIN Equipement e ON e.ID_equipement=i.ID_equipement WHERE i.Origine_donnees=? AND e.ID_equipement IS NULL',(ORIGINE,)).fetchone()[0]==0
    return dict(deja_genere=False,comptes_ajoutes=comptes_ajoutes,pannes_ajoutees=pannes_ajoutees,equipements_suivis=equipements_suivis)


DESCRIPTIONS={
    'Origine_donnees': 'Origine explicite des lignes ajoutées. Simulation predictions v1 : données synthétiques, jamais des observations réelles.',
    'ID_equipement': 'Équipement concerné par l’intervention. Jointure vers Equipement.ID_equipement. NULL pour les anciennes interventions non rattachées.',
    'Indicateur_panne': 'Oui pour une panne datée ; NULL si la nature de l’ancienne intervention est inconnue. Une intervention générique ne prouve pas une panne.',
    'Date_debut_observation': 'Premier jour de couverture du journal de pannes ; vérifier Origine_observation.',
    'Date_fin_observation': 'Dernier jour de couverture complète du journal. Aucun jour ultérieur ne doit être considéré comme observé.',
    'Origine_observation': 'Origine de la couverture du suivi. Simulation predictions v1 : suivi complet généré artificiellement pour la démonstration.',
}


def actualiser_dictionnaire(c,texte):
    for table in ['Releve_compte_client_historique','Equipement','Commande','Intervention']:
        total=c.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        def section(match):
            bloc=re.sub(r'Nombre de lignes : \d+',f'Nombre de lignes : {total}',match[2],count=1)
            for info in c.execute(f'PRAGMA table_info("{table}")').fetchall():
                nom,typ=info[1],info[2]
                nulls,distincts=c.execute(f'SELECT SUM("{nom}" IS NULL),COUNT(DISTINCT "{nom}") FROM "{table}"').fetchone()
                entete=f'- {nom} — Type SQLite : {typ}. NULL observés : {"oui" if nulls else "non"} ({nulls}/{total}). Valeurs distinctes non NULL : {distincts}.'
                pattern=rf'^- {re.escape(nom)} — Type SQLite : [^\n]+'
                if re.search(pattern,bloc,re.M):
                    bloc=re.sub(pattern,lambda _:entete,bloc,flags=re.M)
                else:
                    bloc=bloc.rstrip()+'\n'+entete+'\n   Description : '+DESCRIPTIONS.get(nom,nom)+'\n'
                # Actualiser les effectifs déjà documentés pour cette colonne.
                valeurs=c.execute(f'SELECT "{nom}",COUNT(*) FROM "{table}" WHERE "{nom}" IS NOT NULL GROUP BY 1 ORDER BY COUNT(*) DESC,1 LIMIT 10').fetchall()
                ligne='   Valeurs observées (effectif ; jusqu’à 10 valeurs) : '+' ; '.join(f'{v} ({n})' for v,n in valeurs)
                col_pattern=rf'(^- {re.escape(nom)} —[^\n]*\n)(.*?)(?=^- |\Z)'
                def col(cm):
                    suite=re.sub(r'^   Valeurs observées[^\n]*',lambda _:ligne,cm[2],flags=re.M)
                    return cm[1]+suite
                bloc=re.sub(col_pattern,col,bloc,flags=re.M|re.S)
            return match[1]+bloc+'\n'
        texte=re.sub(rf'(^## {table}[ \t]*\n)(.*?)(?=^## |\Z)',section,texte,flags=re.M|re.S)
    tables=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    total=sum(c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables)
    texte=re.sub(r'La base contient \d+ tables et [\d ]+ lignes au total\.',f'La base contient {len(tables)} tables et {total:,} lignes au total.'.replace(',',' '),texte,count=1)
    if '## Simulation_dataset' not in texte:
        texte+='\n## Simulation_dataset\nNombre de lignes : 1\n'
        for nom in ['ID_simulation','Origine_donnees','Parametres','Date_generation']:
            texte+=f'- {nom} — Type SQLite : TEXT.\n   Description : Métadonnées du générateur reproductible de données fictives.\n'
    note='Les historiques ajoutés portent Origine_donnees ou Origine_observation = « '+ORIGINE+' ». Ils servent uniquement à une démonstration ML. Les données originales sont conservées.'
    if note not in texte:
        texte=texte.replace('## GUIDE D\'UTILISATION',note+'\n\n## GUIDE D\'UTILISATION',1)
    return texte


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,default=ROOT/'DWH_fictive_10000_lignes.sqlite')
    args=p.parse_args()
    base=args.base.resolve()
    if base.parent!=ROOT or not base.is_file():
        raise SystemExit('La base doit être un fichier existant à la racine de ce projet fictif.')
    sauvegardes=ROOT/'.backups'
    sauvegardes.mkdir(exist_ok=True)
    sauvegarde=sauvegardes/f'predictions-avant-enrichissement-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite'
    dico=ROOT/'Dictionnaire_donnees_DWH_fictive_SQLite.md'
    with sqlite3.connect(base,timeout=30) as c:
        c.row_factory=sqlite3.Row
        with sqlite3.connect(sauvegarde) as dest:
            c.backup(dest)
        shutil.copy2(dico,sauvegarde.with_suffix('.md'))
        c.execute('BEGIN IMMEDIATE')
        try:
            result=enrichir(c)
            texte=actualiser_dictionnaire(c,dico.read_text(encoding='utf-8'))
            c.commit()
        except Exception:
            c.rollback()
            raise
    dico.write_text(texte,encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    print('Sauvegarde : '+str(sauvegarde))


if __name__=='__main__':
    main()
