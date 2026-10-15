"""Prototypes ML locaux : projections agrégées et priorité comparative de contrôle.

Les données sources restent en lecture seule. Aucun score individuel de client
ni probabilité de panne physique n'est exposé. Les labels équipements sont des
signalements rapprochés par lot/type, jamais des pannes certifiées.
"""
from collections import Counter, defaultdict
from datetime import date, timedelta
import math
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from boutique.dependencies import user_dep
from boutique.espace import Lecture
from boutique.apprentissage import Ridge, Logistique, aire_roc

router = APIRouter(prefix="/api/espace")
LIMITE_SOURCE = 50000
VARIABLES_IMPAYES = ("Montant_impaye", "Montant_loyer", "Montant_charges",
                     "Montant_paiement_moins_remboursement", "Montant_rejet_prelevement", "Montant_APL")


def jour(valeur):
    try:
        return date.fromisoformat(str(valeur)[:10])
    except (ValueError, TypeError):
        return None


def nombre(valeur):
    try:
        valeur = float(valeur)
        return valeur if math.isfinite(valeur) else None
    except (ValueError, TypeError, OverflowError):
        return None


def mois_suivant(mois):
    return date(mois.year + (mois.month == 12), 1 if mois.month == 12 else mois.month + 1, 1)


def normaliser(valeur):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(valeur or '').lower())
                   if not unicodedata.combining(c)).strip()


def indisponible(raison, **details):
    return dict(disponible=False, raison=raison, **details)


def modele_regression(x, y):
    # Les paramètres de préparation ne sont appris que sur les données d'entraînement.
    return Ridge(alpha=10.0).fit(x,y)


def projection_impayes(lignes, au, variables=VARIABLES_IMPAYES):
    par_mois = defaultdict(dict)
    conflits, invalides = set(), 0
    variables = [v for v in VARIABLES_IMPAYES if v in variables]
    for r in lignes:
        d, client = jour(r.get('Annee_mois')), r.get('ID_client')
        impaye = nombre(r.get('Montant_impaye'))
        if not d or not client or impaye is None or impaye < 0:
            invalides += 1
            continue
        if d > au:
            continue
        m = d.replace(day=1)
        cle = (m, client)
        valeurs = tuple(nombre(r.get(v)) for v in variables)
        if client in par_mois[m] and par_mois[m][client] != valeurs:
            conflits.add(cle)
        par_mois[m][client] = valeurs
    # Une valeur contradictoire n'est ni additionnée ni choisie arbitrairement.
    for m, client in conflits:
        par_mois[m].pop(client, None)
    par_mois = {m: r for m, r in sorted(par_mois.items()) if r}
    audit = dict(mois_disponibles=len(par_mois), lignes_invalides=invalides,
                 client_mois_contradictoires=len(conflits))
    if len(par_mois) < 2:
        return indisponible("Au moins deux mois exploitables sont nécessaires.", audit=audit)
    maximum = max(len(r) for r in par_mois.values())
    complets = [m for m, r in par_mois.items() if len(r) >= .95 * maximum]
    audit['couverture_mensuelle'] = [dict(mois=m.isoformat(), clients=len(r), retenu=m in complets)
                                    for m, r in par_mois.items()]
    if len(complets) < 2:
        return indisponible("Pas assez de mois de couverture comparable (seuil : 95 % du mois le plus fourni).", audit=audit)
    base = complets[-1]
    cible = mois_suivant(base)
    comparables = [m for m in complets if m <= base][-12:]
    cohorte = set.intersection(*(set(par_mois[m]) for m in comparables))
    if len(cohorte) < 30:
        return indisponible("Moins de 30 clients présents sur les mois comparables.", audit=audit)

    def couples(fin):
        resultat = []
        for m in par_mois:
            suivant = mois_suivant(m)
            if suivant > fin or suivant not in par_mois:
                continue
            for ident in sorted(set(par_mois[m]) & set(par_mois[suivant])):
                x = par_mois[m][ident]
                resultat.append((suivant, x, par_mois[suivant][ident][0] - x[0]))
        return resultat

    apprentissage = couples(base)
    if len(apprentissage) < 30:
        return indisponible("Moins de 30 transitions entre deux mois consécutifs pour entraîner le modèle.", audit=audit)
    modele = modele_regression([x for _, x, _ in apprentissage], [y for _, _, y in apprentissage])
    ids = sorted(cohorte)
    entrees = [par_mois[base][ident] for ident in ids]
    deltas = modele.predict(entrees)
    prevus = [max(0.0, x[0] + float(delta)) for x, delta in zip(entrees, deltas)]
    actuel, prevu = sum(x[0] for x in entrees), sum(prevus)

    # Validation chronologique : aucune cible du mois prédit dans l'apprentissage.
    tous = couples(au)
    controle = [p for p in tous if p[0] == cible]
    modele_controle = modele
    if not controle:
        derniers = sorted({m for m, _, _ in apprentissage})
        if len(derniers) >= 2:
            dernier = derniers[-1]
            train = [p for p in apprentissage if p[0] < dernier]
            controle = [p for p in apprentissage if p[0] == dernier]
            if len(train) >= 30:
                modele_controle = modele_regression([x for _, x, _ in train], [y for _, _, y in train])
            else:
                controle = []
    validation = dict(disponible=False, raison="Pas de période ultérieure suffisante pour un test chronologique.")
    if len(controle) >= 10:
        estimations = modele_controle.predict([x for _, x, _ in controle])
        vrais = [x[0] + y for _, x, y in controle]
        preds = [max(0.0, x[0] + float(p)) for (_, x, _), p in zip(controle, estimations)]
        mae = sum(abs(a-b) for a,b in zip(vrais,preds)) / len(vrais)
        reference = sum(abs(y) for _, _, y in controle) / len(controle)
        validation = dict(disponible=True, mois=controle[0][0].isoformat(), observations=len(controle),
                          erreur_moyenne_euros=round(mae,2), erreur_reference_euros=round(reference,2),
                          ameliore_reference=mae < reference)

    historique = [dict(mois=m.isoformat(), montant=round(sum(par_mois[m][ident][0] for ident in ids),2))
                  for m in comparables]
    limites = ["Prototype sur une base fictive ; aucune décision individuelle ni relance automatique.",
               "Périmètre fixe : seuls les clients présents sur tous les mois comparés sont agrégés.",
               "Un mois est retenu si sa couverture atteint 95 % du mois le plus fourni ; cela ne certifie pas sa complétude.",
               "Aucun intervalle de confiance calibré n'est affiché ; un test sur une période ne démontre pas la fiabilité en situation réelle."]
    if cible < au.replace(day=1):
        limites.append("Projection historique : les données sont trop anciennes pour prévoir le prochain mois actuel.")
    if validation.get('disponible') and not validation['ameliore_reference']:
        limites.append("Sur le test disponible, le modèle n'améliore pas la référence « impayé inchangé ».")
    return dict(disponible=True, statut="expérimental", methode="Régression Ridge sur l'évolution mensuelle",
                variables=variables, clients=len(ids), transitions_apprentissage=len(apprentissage),
                derniere_cible_apprentissage=max(m for m,_,_ in apprentissage).isoformat(),
                mois_base=base.isoformat(), mois_projection=cible.isoformat(),
                projection_historique=cible < au.replace(day=1), montant_actuel=round(actuel,2),
                montant_prevu=round(prevu,2), variation_euros=round(prevu-actuel,2),
                variation_pourcent=round(100*(prevu-actuel)/actuel,1) if actuel else None,
                historique=historique, validation=validation, audit=audit, limites=limites)


TYPES_INTERVENTION = {'ASC': 'ascenseur', 'VMC': 'vmc', 'ELE': 'tableau electrique'}
PANNE = re.compile(r'\bhs\b|\bpanne\b|hors\s+service|defaill|en\s+defaut')
ABSENCE_PANNE = re.compile(r'\b(?:sans|aucune?|pas de)\s+(?:panne|defaut)|\bpas\s+(?:hs|hors service)|\bnon\s+hs\b')
OBJETS_TYPES = {'ascenseur': re.compile(r'ascenseur'), 'vmc': re.compile(r'\bvmc\b|ventilation'),
                'tableau electrique': re.compile(r'tableau.{0,20}electri')}


def signaux_equipements(equipements, lots, interventions, au):
    par_lot = defaultdict(set)
    for r in lots:
        if r.get('ID_lot'):
            par_lot[(r.get('Code_societe'), r.get('Code_lot'))].add(r['ID_lot'])
    candidats = defaultdict(list)
    inventaire, ids_vus, conflits_equipements = [], {}, 0
    for r in equipements:
        ident = r.get('ID_equipement')
        if ident:
            ids_vus.setdefault(ident,[]).append(r)
    for ident, groupe in ids_vus.items():
        if any(r != groupe[0] for r in groupe[1:]):
            conflits_equipements += 1
            continue
        r = groupe[0]
        installation = jour(r.get('Date_mise_en_service'))
        fin = jour(r.get('Date_fin_de_service'))
        correspondances = par_lot[(r.get('Code_societe'), r.get('Code_lot'))]
        e = dict(r, installation=installation, fin=fin,
                 lot=next(iter(correspondances)) if len(correspondances)==1 else None,
                 type_normalise=normaliser(r.get('Libelle_type_equipement')))
        inventaire.append(e)
        if e['lot'] and installation:
            candidats[(e['lot'],e['type_normalise'])].append(e)
    dates, signaux, ignores, ambigus = [], defaultdict(list), 0, 0
    # Les jointures contradictoires d'une intervention ne fournissent aucun label.
    groupes = defaultdict(list)
    for r in interventions:
        groupes[r.get('ID_intervention')].append(r)
    for ident, groupe in groupes.items():
        versions = {tuple((k,str(v)) for k,v in sorted(r.items())) for r in groupe}
        if not ident or len(versions)!=1:
            ambigus += 1
            continue
        r = groupe[0]
        d = jour(r.get('Date_realisation_intervention'))
        if not d or d > au:
            continue
        dates.append(d)
        typ = TYPES_INTERVENTION.get(str(r.get('Code_intervention') or '').upper())
        objet = normaliser(r.get('objet'))
        if not typ or not PANNE.search(objet) or ABSENCE_PANNE.search(objet) or not OBJETS_TYPES[typ].search(objet):
            continue  # Un contrôle périodique n'est jamais étiqueté « panne ».
        possibles = [e for e in candidats[(r.get('ID_lot'),typ)]
                     if e['installation'] <= d and (not e['fin'] or d <= e['fin'])]
        if len(possibles)==1:
            signaux[possibles[0]['ID_equipement']].append(d)
        elif len(possibles)>1:
            ambigus += 1
        else:
            ignores += 1
    return inventaire, signaux, dates, dict(signaux_rapproches=sum(map(len,signaux.values())),
                                           signaux_sans_equipement=ignores, rapprochements_ambigus=ambigus,
                                           equipements_contradictoires=conflits_equipements)


def signaux_directs(equipements,lots,interventions,au):
    inventaire,_,_,audit=signaux_equipements(equipements,lots,[],au)
    par_id={e['ID_equipement']:e for e in inventaire}
    dates,signaux= [],defaultdict(list)
    for e in inventaire:
        e['observation_debut']=jour(e.get('Date_debut_observation'))
        fin=jour(e.get('Date_fin_observation'))
        e['observation_fin']=min(fin,au) if fin else None
        if e['observation_debut'] and e['observation_fin'] and e['observation_debut']<e['observation_fin']:
            dates.extend([e['observation_debut'],e['observation_fin']])
    groupes=defaultdict(list)
    for r in interventions:
        groupes[r.get('ID_intervention')].append(r)
    exclus=0
    for ident,groupe in groupes.items():
        if not ident or any(r!=groupe[0] for r in groupe[1:]):
            exclus+=1
            continue
        r=groupe[0]
        e=par_id.get(r.get('ID_equipement'))
        d=jour(r.get('Date_realisation_intervention'))
        if r.get('Indicateur_panne')!='Oui' or not d or d>au:
            continue
        if not e or not e['installation'] or not e['observation_debut'] or not e['observation_fin'] or not (
                max(e['installation'],e['observation_debut'])<=d<=e['observation_fin']):
            exclus+=1
            continue
        signaux[e['ID_equipement']].append(d)
    pannes=[d for ds in signaux.values() for d in ds]
    audit.update(signaux_rapproches=len(pannes),pannes_exclues=exclus,
        premiere_intervention=min(pannes).isoformat() if pannes else None,
        derniere_intervention=max(pannes).isoformat() if pannes else None,
        debut_observation=min(dates).isoformat() if dates else None,
        fin_observation=max(dates).isoformat() if dates else None)
    return inventaire,signaux,dates,audit


def indice_equipements(equipements, lots, interventions, au, directs=False):
    if directs:
        inventaire,signaux,dates,audit=signaux_directs(equipements,lots,interventions,au)
    else:
        inventaire, signaux, dates, audit = signaux_equipements(equipements,lots,interventions,au)
    if not dates:
        return indisponible("Aucun historique d'intervention daté exploitable.", audit=audit)
    debut, fin = min(dates), max(dates)
    audit['equipements']=len(inventaire)
    audit.setdefault('premiere_intervention',debut.isoformat())
    audit.setdefault('derniere_intervention',fin.isoformat())
    date_score=min(au,fin) if directs else au
    periodes, courant = [], debut
    while courant+timedelta(days=90)<=fin:
        periodes.append(courant)
        courant += timedelta(days=90)
    if len(periodes)<2:
        return indisponible("Moins de deux fenêtres complètes de 90 jours pour apprendre et tester.", audit=audit)
    types = Counter()
    for e in inventaire:
        types[e['type_normalise']] += sum(v<=periodes[-1] for v in signaux[e['ID_equipement']])
    couverts = {t for t,n in types.items() if n>=10}
    if not couverts:
        return indisponible("Moins de 10 signalements rapprochables par type avant le test : risque de panne non estimable.", audit=audit)

    def disponible(e, d):
        return e['type_normalise'] in couverts and e['lot'] and e['installation'] and e['installation']<=d and (not e['fin'] or e['fin']>d)

    def couvert(e,d,fin_periode):
        return not directs or (e['observation_debut'] and e['observation_fin'] and
                               e['observation_debut']<=d and fin_periode<=e['observation_fin'])

    def caracteristiques(e, d):
        passes = sorted(v for v in signaux[e['ID_equipement']] if v<=d)
        return [(d-e['installation']).days/365.25,
                sum(0 <= (d-v).days <= 365 for v in passes),
                sum(0 <= (d-v).days <= 90 for v in passes),
                min((d-passes[-1]).days,730) if passes else 730,
                int(not passes), *[int(e['type_normalise']==t) for t in sorted(couverts)]]
    exemples = []
    for d in periodes[-12:]:
        for e in inventaire:
            if disponible(e,d) and couvert(e,d,d+timedelta(days=90)):
                cible = int(any(d<v<=d+timedelta(days=90) for v in signaux[e['ID_equipement']]))
                exemples.append((d,caracteristiques(e,d),cible))
    if len(exemples)>20000:
        return indisponible("Ce prototype est limité à 20 000 observations équipement/période ; réduisez le périmètre.", audit=audit)
    apprentissage = [p for p in exemples if p[0]<periodes[-1]]
    controle = [p for p in exemples if p[0]==periodes[-1]]
    if len(apprentissage)<50 or sum(y for _,_,y in apprentissage)<10 or len({y for _,_,y in apprentissage})<2:
        return indisponible("Pas assez de signalements et de périodes comparables pour entraîner le modèle.", audit=audit)
    def entrainer(ex):
        return Logistique().fit([x for _,x,_ in ex],[y for _,_,y in ex])
    try:
        modele = entrainer(apprentissage)
    except ValueError:
        return indisponible("Le modèle ne converge pas ; aucun indice de contrôle n'est publié.", audit=audit)
    validation = dict(debut=periodes[-1].isoformat(), fin=(periodes[-1]+timedelta(days=90)).isoformat(),
                      observations=len(controle), signaux_positifs=sum(y for _,_,y in controle), disponible=False)
    if controle and len({y for _,_,y in controle})==2 and validation['signaux_positifs']>=5:
        probabilites = [r[1] for r in modele.predict_proba([x for _,x,_ in controle])]
        validation.update(disponible=True, auc=round(aire_roc([y for _,_,y in controle],probabilites),3))
    else:
        validation['raison']="Moins de cinq signalements positifs sur la période test ; qualité prédictive non établie."
    try:
        modele = entrainer(exemples)
    except ValueError:
        return indisponible("Le modèle ne converge pas ; aucun indice de contrôle n'est publié.", audit=audit)
    eligibles = [e for e in inventaire if disponible(e,date_score) and couvert(e,date_score,date_score) and e.get('Indicateur_activite','Oui')=='Oui']
    if not eligibles:
        return indisponible("Aucun équipement éligible en service à la date choisie.", audit=audit)
    valeurs = [round(float(s),8) for s in modele.decision_function([caracteristiques(e,date_score) for e in eligibles])]
    comptes = Counter(valeurs)
    rangs, avant = {}, 0
    for valeur in sorted(comptes):
        rangs[valeur] = 100*(avant+(comptes[valeur]-1)/2)/max(1,len(valeurs)-1) if len(valeurs)>1 else 50
        avant += comptes[valeur]
    lignes = []
    for e,s in zip(eligibles,valeurs):
        passes = [v for v in signaux[e['ID_equipement']] if v<=date_score]
        lignes.append(dict(ID_equipement=e['ID_equipement'],ID_lot=e['lot'],
            Libelle_type_equipement=e.get('Libelle_type_equipement'),
            Age_equipement=round((date_score-e['installation']).days/365.25,1),
            Indice_priorite=round(rangs[s],1), Signaux_365_jours=sum((date_score-v).days<=365 for v in passes),
            Dernier_signal=max(passes).isoformat() if passes else None))
    lignes.sort(key=lambda r:(-r['Indice_priorite'],r['ID_equipement']))
    couverture = Counter(e['type_normalise'] for e in eligibles)
    limites = ["Indice comparatif de contrôle, pas une probabilité de panne ni un diagnostic de sécurité.",
        "Label indirect : objet de commande mentionnant une panne/HS, rapproché à un seul équipement du même lot et type.",
        "Une période sans signalement ne prouve pas l'absence de panne ; la couverture des interventions n'est pas certifiée.",
        "Les rapprochements ambigus sont exclus. Les types sans au moins 10 signaux restent non estimables.",
        "Prototype sur données fictives, à confirmer par un historique de pannes lié à ID_equipement."]
    if directs:
        limites=["Indice comparatif de contrôle, pas une probabilité calibrée de panne réelle.",
            "Pannes explicitement datées et liées à ID_equipement ; seules les fenêtres couvertes par le suivi sont utilisées.",
            "Les historiques et leur couverture sont simulés. Un résultat sur cette simulation ne valide pas le modèle sur des équipements réels.",
            "Les types avec moins de 10 pannes avant la période test restent non estimables.",
            "Le score est calculé au dernier jour couvert ; les jours suivants ne sont pas considérés comme observés."]
    if not validation['disponible']:
        limites.append(validation['raison'])
    return dict(disponible=True, statut="expérimental — pannes liées à l’équipement" if directs else "expérimental — label indirect",
        mode_labels='directs' if directs else 'indirects',methode="Régression logistique, horizon 90 jours",
        date_reference_modele=date_score.isoformat(),horizon_jours=90, jusqu_au=(date_score+timedelta(days=90)).isoformat(), equipements_estimables=len(eligibles),
        equipements_non_estimables=len(inventaire)-len(eligibles),
        couverture=[dict(type=t, total=n, estimables=couverture[t]) for t,n in Counter(e['type_normalise'] for e in inventaire).items()],
        exemples_apprentissage=len(exemples), audit=audit, validation=validation, limites=limites,
        resultats=dict(columns=list(lignes[0]),rows=lignes[:100],row_count=min(len(lignes),100),truncated=len(lignes)>100))


def source(lecture, table, colonnes, condition='1=1', args=()):
    sql = 'SELECT '+','.join('"'+c+'"' for c in colonnes)+' FROM "'+table+'" WHERE '+condition
    r = lecture.requete(sql,args,limite=LIMITE_SOURCE)
    if r['truncated']:
        raise HTTPException(413,"Trop de données pour ce prototype ; aucun modèle n'est entraîné sur une extraction tronquée.")
    return r['rows']


@router.get('/predictions')
def predictions(au: date = Query(), u=Depends(user_dep)):
    lecture = Lecture(u)
    impayes = indisponible("Les colonnes nécessaires aux impayés ne sont pas accessibles à votre service.")
    equipements = indisponible("Les tables ou colonnes nécessaires au rapprochement des équipements ne sont pas accessibles à votre service.")
    table = 'Releve_compte_client_historique'
    if lecture.permet(table,'ID_client','Annee_mois','Montant_impaye'):
        variables = [v for v in VARIABLES_IMPAYES if lecture.permet(table,v)]
        lignes = source(lecture,table,['ID_client','Annee_mois',*variables])
        impayes = projection_impayes(lignes,au,variables)
    requis = {
        'Equipement':['ID_equipement','Code_societe','Code_lot','Libelle_type_equipement','Date_mise_en_service'],
        'Lot':['ID_lot','Code_societe','Code_lot'],
        'Intervention':['ID_intervention','ID_commande','ID_lot','Code_intervention','Date_realisation_intervention'],
        'Commande':['ID_commande','Libelle_objet_commande_1'],
    }
    observation=['Date_debut_observation','Date_fin_observation','Origine_observation']
    pannes_directes=['ID_intervention','ID_equipement','Indicateur_panne','Date_realisation_intervention']
    acces_base=all(lecture.permet(t,*requis[t]) for t in ['Equipement','Lot'])
    acces_direct=acces_base and lecture.permet('Equipement',*observation) and lecture.permet('Intervention',*pannes_directes)
    acces_indirect=all(lecture.permet(t,*cols) for t,cols in requis.items())
    if acces_direct or acces_indirect:
        cols = requis['Equipement']+[v for v in ('Date_fin_de_service','Indicateur_activite',*observation) if lecture.permet('Equipement',v)]
        es = source(lecture,'Equipement',cols)
        lots = source(lecture,'Lot',requis['Lot'])
        if acces_direct and any(e.get('Date_debut_observation') and e.get('Date_fin_observation') for e in es):
            evenements=source(lecture,'Intervention',pannes_directes,'"ID_equipement" IS NOT NULL')
            equipements=indice_equipements(es,lots,evenements,au,directs=True)
        elif acces_indirect:
            r = lecture.requete('SELECT i.ID_intervention,i.ID_lot,i.Code_intervention,i.Date_realisation_intervention,'
                'c.Libelle_objet_commande_1 AS objet FROM Intervention i JOIN Commande c ON c.ID_commande=i.ID_commande',limite=LIMITE_SOURCE)
            if r['truncated']:
                raise HTTPException(413,"Historique trop volumineux ; aucun entraînement sur un historique tronqué.")
            equipements = indice_equipements(es,lots,r['rows'],au)
    return lecture.terminer(dict(au=au.isoformat(), demonstration=True, impayes=impayes,equipements=equipements))
