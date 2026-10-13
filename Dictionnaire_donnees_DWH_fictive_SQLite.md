DICTIONNAIRE DE DONNÉES
Base fictive DWH — SQLite
Ce document décrit la structure de la base SQLite générée à partir du script de données fictives. Version 2 : enrichie (guide d'utilisation, jointures validées, valeurs observées par colonne, anomalies connues). La base contient 28 tables et 10 000 lignes au total.

## GUIDE D'UTILISATION (à lire avant d'écrire une requête)

### 1. Règles de requêtage
1. Noms exacts : utiliser les noms de tables et colonnes tels qu'écrits ici. Sept colonnes ont un accent ou un espace et doivent être entre guillemets ("…" en SQLite, […] en SQL Server) : Affaire."Code_société", Affaire."Indicateur_validité_objet", Affaire."Date_théorique_prise_en_charge", Affaire."Indicateur_validité_affectation", Affaire."Lien_IKOS synthese_affaire", Bail."Nombre_jours_delais_prévis", Patrimoine."Code_département". Attention : Geographie utilise Code_departement (sans accent) et Affaire utilise Code_société alors que les autres tables utilisent Code_societe.
2. Dates : stockées en TEXT. Formats : AAAA-MM-JJ ou AAAA-MM-JJ hh:mm:ss.fff (Date_actualisation). Les colonnes Annee_mois contiennent en réalité une date du 1er du mois (ex. 2025-02-01) et Annee une date du 1er janvier (ex. 2025-01-01), pas AAAA-MM ni AAAA. Pour filtrer une année ou un mois, utiliser substr(col,1,4) / substr(col,1,7) ou un intervalle de dates.
3. Dates sentinelles : 2099-12-31 (fin d'occupation) et 2099-01-01 (réception de préavis) signifient « non renseigné / en cours ». Ne pas les traiter comme de vraies dates dans un calcul de durée.
4. Booléens et statuts : valeurs texte, comparer à l'égalité exacte, accents et casse compris : 'Oui' / 'Non' pour la plupart des Indicateur_* ; Bail.Indicateur_occupation_active = 'Actif' / 'Inactif' ; Client.Indicateur_statut_presence = 'Présent' / 'Parti'. Avant de filtrer sur une colonne catégorielle, relire sa ligne « Valeurs observées » : les libellés de la base ne sont pas toujours ceux de la documentation fonctionnelle (ex. 'Proprete/Incivilite' sans accent, 'Sortie Etat des lieux', 'Enquete').
5. Identifiants : ID_lot = Code_societe-Code_lot (AJ-000001) ; ID_client = Code_societe-Code_client (AJ-003301) ; ID_client_lot = CLT-<ID_client>-LOT-<ID_lot> ; ID_diagnostic = Code_societe-Numero_diagnostic (AJ-018769) ; ID_occupant = <ID_client>-OCC-nnnn. Les codes (Code_lot, Numero_diagnostic…) sont des chaînes de 6 chiffres avec zéros initiaux : les comparer comme du texte ('000001'), jamais comme des nombres.
6. Grain et doublons : vérifier le grain de chaque table (section 3) avant de joindre. Client est au grain client × lot, donc joindre une table enfant à Client sur ID_client multiplie les lignes. Utiliser SELECT DISTINCT ou COUNT(DISTINCT …) sur l'identifiant de l'entité recherchée.
7. Pas de contraintes dans le fichier SQLite (ni PRIMARY KEY, ni FOREIGN KEY) : les relations ci-dessous ont été vérifiées sur les données (0 orphelin) mais ne sont pas imposées par le moteur.
8. Colonne Valeur de Diagnostic_valeur : type mixte, voir la fiche de la table.
9. Si une requête renvoie 0 ligne : la rejouer en ajoutant une jointure à la fois avec COUNT(*), puis vérifier avec SELECT DISTINCT col, COUNT(*) … GROUP BY col que chaque valeur filtrée existe bien (et pour la combinaison des filtres, pas seulement pour chacun séparément). La plupart des « zéro résultat » viennent d'une combinaison de filtres impossible dans les données, pas d'une erreur de jointure.

### 2. Valeurs de référence : correspondance Type_valeur × Famille_diagnostic (état de la base)
Les valeurs de Diagnostic_valeur sont rattachées à des familles de diagnostic de façon non conforme à la logique métier (anomalie n°1). Familles de Diagnostic portant effectivement chaque Type_valeur :

| Type_valeur | Familles de diagnostic présentes dans la base |
|---|---|
| Lettre_DPE_EP | CREP, DTA, EIIG, RAAT LO TOITURE |
| Valeur_CREP | DAPP, EIIE, RAAT LO, RAAT ST |
| Valeur_DAPP | DPE, EIIE, RAAT LO FACADE, RAAT ST |
| Valeur_DTA_liste_A_1 | CREP, DPE, EIIG, RAAT LO FACADE |
| Valeur_EIIE | DAPP, DTA, RAAT LO, RAAT LO TOITURE |

Conséquence : le couple Famille_diagnostic = 'DPE' et Type_valeur = 'Lettre_DPE_EP' n'existe dans aucune ligne.

### 3. Grain des tables et clés (toutes vérifiées uniques)
| Table | Une ligne par… | Clé unique |
|---|---|---|
| Organisation | entité d'organisation | ID_organisation |
| Collaborateur | collaborateur | Code_collaborateur |
| Patrimoine | patrimoine | ID_patrimoine |
| Organisation_patrimoine_pivot | patrimoine rattaché à une organisation | ID_patrimoine |
| Geographie | commune | Code_INSEE_commune |
| Lot | lot (un ID_client_lot par lot dans cette base) | ID_lot ; ID_client_lot |
| Patrimoine_lot_pivot | lot d'un patrimoine | ID_patrimoine_lot |
| Client | client × lot, donc ID_client NON unique (320 pour 400 lignes) | ID_client_lot |
| Client_lot_pivot | rattachement client × lot | ID_client_lot |
| Occupant | occupant (plusieurs par client possible) | ID_occupant |
| Bail | bail | ID_bail |
| Client_historique, Contentieux_client_historique, Releve_compte_client_historique | client × mois | ID_client_annee_mois |
| Lot_historique | lot × mois | ID_lot_annee_mois |
| Affaire | affaire | ID_Affaire |
| Affaire_pivot | lien affaire × client_lot | ID_Affaire |
| Commande | commande | ID_commande |
| Commande_lot_pivot | lien commande × lot | ID_commande |
| Intervention | intervention (plusieurs par commande) | ID_intervention |
| Diagnostic | diagnostic (un seul par lot ; 150 lots n'en ont aucun) | ID_diagnostic |
| Diagnostic_valeur | valeur d'un diagnostic (2 par diagnostic) | (ID_diagnostic, Type_valeur) |
| Reglementation | lot (une seule ligne par lot) | ID_lot |
| Equipement | équipement | ID_equipement |
| Piece | pièce | ID_piece |
| Copropriete | copropriété | ID_copropriete |
| Copropriete_resolution | résolution (2 par copropriété) | ID_copropriete + Numero_resolution_tri |
| Calendrier | jour | Date |

### 4. Jointures validées (0 orphelin dans les données)
Lot est la table centrale ; Client / Client_lot_pivot portent la relation client × lot.

| De | Vers | Colonnes | Cardinalité |
|---|---|---|---|
| Lot | Patrimoine | ID_patrimoine | N → 1 |
| Patrimoine | Organisation | ID_organisation | N → 1 |
| Patrimoine | Geographie | Code_INSEE_commune | 1 → 1 |
| Patrimoine_lot_pivot | Lot | ID_lot | 1 → 1 |
| Patrimoine_lot_pivot | Patrimoine | ID_patrimoine | N → 1 |
| Equipement | Patrimoine_lot_pivot | ID_patrimoine_lot | 1 → 1 |
| Client_lot_pivot | Client | ID_client_lot (ou ID_client, attention au grain) | 1 → 1 sur ID_client_lot |
| Client_lot_pivot | Lot | ID_lot | 1 → 1 |
| Occupant | Client_lot_pivot | ID_client | N → N (un client peut avoir plusieurs lots et plusieurs occupants) : utiliser DISTINCT |
| Bail | Lot / Client | ID_client_lot ou ID_lot / ID_client | 1 → 1 |
| Client_historique, Contentieux_client_historique, Releve_compte_client_historique | Client | ID_client | N → N (Client non unique sur ID_client) : passer par Client_lot_pivot si le grain compte |
| Lot_historique | Lot | ID_lot | N → 1 |
| Affaire | Lot / Patrimoine / Organisation / Client | ID_lot / ID_patrimoine / ID_organisation / ID_client_demandeur_affaire = ID_client | N → 1 |
| Affaire_pivot | Affaire / Lot | ID_Affaire / ID_client_lot (= Lot.ID_client_lot) | 1 → 1 |
| Commande | Organisation | ID_organisation | N → 1 |
| Commande_lot_pivot | Commande / Lot | ID_commande / ID_lot | 1 → 1 |
| Intervention | Commande | ID_commande | N → 1 (jusqu'à 2 interventions par commande) |
| Intervention | Lot | ID_lot | 1 → 1 |
| Diagnostic | Lot | ID_lot | 1 → 1 |
| Diagnostic_valeur | Diagnostic | ID_diagnostic (ou Code_societe + Numero_diagnostic) | N → 1 (2 valeurs par diagnostic) |
| Reglementation | Lot | ID_lot | 1 → 1 |
| Piece | Lot | ID_lot | 1 → 1 |
| Copropriete | Patrimoine | ID_patrimoine | 1 → 1 |
| Copropriete_resolution | Copropriete / Patrimoine | ID_copropriete / ID_patrimoine | N → 1 |
| Collaborateur | Organisation | ID_organisation | 1 → 1 |
| Organisation_patrimoine_pivot | Organisation / Patrimoine | ID_organisation / ID_patrimoine | N → 1 |

### 5. Exemple de requête courante : occupants de lots dont l'étiquette DPE (énergie primaire) est F ou G
```sql
SELECT DISTINCT o.ID_occupant, o.Nom_occupant, o.Prenom_occupant
FROM Occupant o
JOIN Client_lot_pivot clp ON clp.ID_client = o.ID_client
JOIN Diagnostic d         ON d.ID_lot = clp.ID_lot
JOIN Diagnostic_valeur dv ON dv.ID_diagnostic = d.ID_diagnostic
WHERE dv.Type_valeur = 'Lettre_DPE_EP'
  AND dv.Valeur IN ('F','G');   -- pas de filtre sur Famille_diagnostic (anomalie n°1)
```
Renvoie 57 occupants dans la base actuelle. Ajouter AND d.Famille_diagnostic = 'DPE' donne 0 ligne.

### 6. Anomalies connues des données fictives
1. Incohérence Diagnostic ↔ Diagnostic_valeur : Famille_diagnostic, Nature_diagnostic, Libelle_diagnostic et Type_valeur sont affectés de façon indépendante. Type_valeur = 'Lettre_DPE_EP' est rattaché aux familles CREP, DTA, EIIG et RAAT LO TOITURE, jamais à 'DPE'. Les diagnostics de famille 'DPE' portent Valeur_DAPP et Valeur_DTA_liste_A_1. Le libellé de la famille 'DPE' est « RAAT Façade ».
2. Diagnostic_valeur.Valeur : type mixte (REAL et TEXT) ; Unite sans lien avec Type_valeur.
3. Tous les diagnostics ont Indicateur_diagnostic_perime = 'Oui' et leur Date_fin_diagnostic est en 2024-2025 ; Indicateur_diagnostic_le_plus_recent vaut 'Oui' pour 84 diagnostics seulement.
4. Client n'est pas unique sur ID_client (320 pour 400 lignes) : risque de doublons après jointure.
5. Les libellés de la base diffèrent parfois de la documentation fonctionnelle (accents supprimés, modalités restreintes). Les modalités réelles sont données dans les lignes « Valeurs observées » de chaque colonne.
6. Colonne documentée « Annee_mois : AAAA-MM » : en réalité AAAA-MM-01 (idem Annee : AAAA-01-01).
7. Les répartitions sont artificielles (effectifs identiques ou quasi identiques entre modalités, ex. 80 / 100 / 320) : ne pas en tirer d'interprétation statistique.
8. Certaines colonnes « Format / valeurs indicatives » décrivent le DWH réel (ex. « 1 à 976 », « Prénom NOM ») et non les valeurs de cette base : la ligne « Valeurs observées » / « Format observé » prévaut pour écrire un filtre.

## Périmètre et conventions
- Les noms de tables et de colonnes sont ceux présents dans le fichier SQLite.
- Les descriptions fonctionnelles et formats indicatifs proviennent du dictionnaire DWH fourni, lorsqu’un champ correspondant y est documenté.
- Les types indiqués comme « type SQLite » sont ceux déclarés dans la base. SQLite étant flexible sur les types, ils décrivent l’affinité déclarée et non une garantie stricte sur chaque valeur.
- Le fichier SQLite importé ne définit pas de contraintes PRIMARY KEY ni FOREIGN KEY. Les identifiants et relations fonctionnels décrits dans ce document ne sont donc pas nécessairement imposés par le moteur.
- La nullabilité présentée reflète les valeurs observées dans les données importées : « Oui » signifie qu’au moins une valeur NULL a été observée ; « Non » signifie qu’aucune valeur NULL n’a été observée dans cette extraction. Cela ne constitue pas une contrainte de schéma.

## Politique de confidentialité
Les lignes « Confidentialité : RGPD » constituent une classification technique
conservatrice : identifiants de personnes, coordonnées, données individuelles,
liens vers des dossiers et champs libres susceptibles de contenir des informations
personnelles. Le serveur MCP bloque ces colonnes par défaut, y compris dans les
filtres et jointures. Les agrégats sur colonnes non marquées restent possibles.
Cette classification doit être réexaminée lors de tout changement de schéma.
Les droits web restent configurés explicitement par service dans l'administration.

## Sommaire des tables
- Affaire — 300 lignes
- Affaire_pivot — 300 lignes
- Bail — 400 lignes
- Calendrier — 731 lignes
- Client — 400 lignes
- Client_historique — 900 lignes
- Client_lot_pivot — 400 lignes
- Collaborateur — 30 lignes
- Commande — 300 lignes
- Commande_lot_pivot — 300 lignes
- Contentieux_client_historique — 400 lignes
- Copropriete — 80 lignes
- Copropriete_resolution — 160 lignes
- Diagnostic — 250 lignes
- Diagnostic_valeur — 500 lignes
- Equipement — 400 lignes
- Geographie — 100 lignes
- Intervention — 400 lignes
- Lot — 400 lignes
- Lot_historique — 900 lignes
- Occupant — 400 lignes
- Organisation — 30 lignes
- Organisation_patrimoine_pivot — 80 lignes
- Patrimoine — 80 lignes
- Patrimoine_lot_pivot — 400 lignes
- Piece — 250 lignes
- Reglementation — 400 lignes
- Releve_compte_client_historique — 709 lignes

## Affaire
Nombre de lignes : 300
- ID_Affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Identifiant de l'affaire
   Format / valeurs indicatives : Code_societe-Code_affaire (AC-608983)
   Exemples : AJ-608983 ; AC-608984 ; BSH-608985
- ID_client_demandeur_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Identifiant du client demandeur
   Format / valeurs indicatives : Code_societe-Code_client_demandeur_affaire (AC-057897)
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Lot concerné
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 80.
   Description : Patrimoine concerné
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- ID_organisation — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Description : Organisation en charge
   Format / valeurs indicatives : AC-R2-01-08
   Exemples : AJ-R1-01-01 ; AC-R2-02-02 ; BSH-R3-03-03
- Code_société — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (75) ; BSH (75) ; AJ (75) ; AC (75)
- Code_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Code de l'affaire
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 608983 ; 608984 ; 608985
   Format observé : 999999 (ex. 608983)
- Code_client_demandeur_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Code du client demandeur
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 003301 ; 003302 ; 003303
   Format observé : 999999 (ex. 003301)
- Code_mode_contact — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 6.
   Description : Code du mode de contact
   Format / valeurs indicatives : 24H / VST / CRR / MEL / TEL / VSS
   Exemples : 24H ; VST ; CRR
   Valeurs observées (effectif) : VST (50) ; VSS (50) ; TEL (50) ; MEL (50) ; CRR (50) ; 24H (50)
- Libelle_mode_contact — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 6.
   Description : Libellé du mode de contact
   Format / valeurs indicatives : Service 24h/24 / Téléphone / Courrier / Visite sur site / E-mail / Accueil / NULL
   Exemples : Service 24h/24 ; Visite sur site ; Courrier
   Valeurs observées (effectif) : Visite sur site (50) ; Téléphone (50) ; Service 24h/24 (50) ; E-mail (50) ; Courrier (50) ; Accueil (50)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Code du lot
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Code_lot_principale_ATR — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Code du lot principal (ATR)
   Format / valeurs indicatives : Code à 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 80.
   Description : Patrimoine niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères (lettres majuscules et chiffres)
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 9.
   Description : Patrimoine niveau 2
   Format / valeurs indicatives : 1 à 3 caractères (lettres majuscules et chiffres)
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 06 (34) ; 05 (34) ; 04 (34) ; 03 (34) ; 02 (34) ; 01 (34) ; 08 (33) ; 07 (33) ; 09 (30)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 12.
   Description : Patrimoine niveau 3
   Format / valeurs indicatives : 1 à 3 caractères (lettres majuscules et chiffres)
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (26) ; 07 (26) ; 06 (26) ; 05 (26) ; 04 (26) ; 03 (26) ; 02 (26) ; 01 (26) ; 12 (23) ; 11 (23) ; 10 (23) ; 09 (23)
- Code_niveau_organisation_1 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 8.
   Description : Organisation niveau 1
   Format / valeurs indicatives : 2 à 4 caractères (lettres majuscules et chiffres)
   Exemples : R1 ; R2 ; R3
   Valeurs observées (effectif) : R6 (40) ; R5 (40) ; R4 (40) ; R3 (40) ; R2 (40) ; R1 (40) ; R8 (30) ; R7 (30)
- Code_niveau_organisation_2 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 9.
   Description : Organisation niveau 2
   Format / valeurs indicatives : 01 / 02 / 03 / 04 / 05 / 09 / BR
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 03 (40) ; 02 (40) ; 01 (40) ; 09 (30) ; 08 (30) ; 07 (30) ; 06 (30) ; 05 (30) ; 04 (30)
- Code_niveau_organisation_3 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 12.
   Description : Organisation niveau 3
   Format / valeurs indicatives : 01 / 02 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 11 / 12
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 06 (30) ; 05 (30) ; 04 (30) ; 03 (30) ; 02 (30) ; 01 (30) ; 12 (20) ; 11 (20) ; 10 (20) ; 09 (20) ; 08 (20) ; 07 (20)
- Code_nature_processus — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Nature du processus
   Format / valeurs indicatives : AFF
   Exemples : AFF
   Valeurs observées (effectif) : AFF (300)
- Code_processus — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Code du processus
   Format / valeurs indicatives : Code à 9 chiffres
   Exemples : 100000000 ; 100000001 ; 100000002
   Format observé : 999999999 (ex. 100000000)
- Code_categorie_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 9.
   Description : Code de catégorie
   Format / valeurs indicatives : SAV / SAR / SAG / RCO / TEC / TEP / TSP / EDL / ADM
   Exemples : SAV ; SAR ; SAG
   Valeurs observées (effectif) : SAV (34) ; SAR (34) ; SAG (34) ; TSP (33) ; TEP (33) ; TEC (33) ; RCO (33) ; EDL (33) ; ADM (33)
- Libelle_categorie_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 8.
   Description : Libellé de catégorie
   Format / valeurs indicatives : Technique / Réclamation Copropriété / SAV Réha / SAV GE / Sortie État des lieux / Administrative / Travaux cofinancés / SAV promo
   Exemples : Technique ; Réclamation Copropriété ; SAV Réha
   Valeurs observées (effectif) : Technique (67) ; SAV Réha (34) ; Réclamation Copropriété (34) ; Travaux cofinancés (33) ; Sortie Etat des lieux (33) ; SAV promo (33) ; SAV GE (33) ; Administrative (33)
- Code_type_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 3.
   Description : Code du type d'affaire
   Format / valeurs indicatives : 3 caractères (lettres et chiffres)
   Exemples : TEC ; ADM ; SAV
   Valeurs observées (effectif) : TEC (100) ; SAV (100) ; ADM (100)
- Libelle_type_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 3.
   Description : Libellé du type d'affaire
   Format / valeurs indicatives : Composteurs, Gérant Immobilier, Propreté/Incivilité, Salage ou déneigement…
   Exemples : Composteurs ; Gerant Immobilier ; Proprete/Incivilite
   Valeurs observées (effectif) : Proprete/Incivilite (100) ; Gerant Immobilier (100) ; Composteurs (100)
- Code_etat_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 4.
   Description : Code d'état
   Format / valeurs indicatives : ENR / CLO / ANN / ENC / TRT / ENG
   Exemples : ENC ; CLO ; TRT
   Valeurs observées (effectif) : TRT (75) ; ENR (75) ; ENC (75) ; CLO (75)
- Libelle_etat_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 4.
   Description : Libellé d'état
   Format / valeurs indicatives : Clos / En cours / Affaire traitée / Engagé / Enregistré / Annulé
   Exemples : En cours ; Clos ; Affaire traitée
   Valeurs observées (effectif) : Enregistré (75) ; En cours (75) ; Clos (75) ; Affaire traitée (75)
- Indicateur_statut_etat_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 2.
   Description : Statut ouvert/fermé
   Format / valeurs indicatives : Ouvert / Fermé
   Exemples : Ouvert ; Fermé
   Valeurs observées (effectif) : Ouvert (225) ; Fermé (75)
- Rang_etape — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 5.
   Description : Rang de l'étape courante
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 5 (60) ; 4 (60) ; 3 (60) ; 2 (60) ; 1 (60)
- Code_etape — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 5.
   Description : Code de l'étape
   Format / valeurs indicatives : 6 lettres majuscules
   Exemples : PRC ; EDL ; CRC
   Valeurs observées (effectif) : TRT (60) ; PRC (60) ; EDL (60) ; CRC (60) ; CLO (60)
- Libelle_etape — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 5.
   Description : Libellé de l'étape
   Format / valeurs indicatives : 3-Pr en charge CSR, Etat des lieux, 1-Prise en charge CRC…
   Exemples : 3-Pr en charge CSR ; Etat des lieux ; 1-Prise en charge CRC
   Valeurs observées (effectif) : Traitement (60) ; Etat des lieux (60) ; Cloture (60) ; 3-Pr en charge CSR (60) ; 1-Prise en charge CRC (60)
- Code_objet_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Code de l'objet
   Format / valeurs indicatives : 3 chiffres
   Exemples : 100 ; 101 ; 102
   Format observé : 999 (ex. 100)
- Libelle_objet_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Libellé de l'objet
   Format / valeurs indicatives : Plainte voisinage
   Exemples : Plainte voisinage
   Valeurs observées (effectif) : Plainte voisinage (300)
- Indicateur_validité_objet — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Objet valide
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (300)
- Libelle_commentaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Commentaire de l'affaire
   Format / valeurs indicatives : Texte libre
   Exemples : Commentaire affaire 1 ; Commentaire affaire 2 ; Commentaire affaire 3
- Date_ouverture — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Date d'ouverture
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-01 ; 2025-01-02 ; 2025-01-03
   Format observé : AAAA-MM-JJ
- Date_enregistrement — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Date d'enregistrement
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-02 ; 2025-01-03 ; 2025-01-04
   Format observé : AAAA-MM-JJ
- Date_prise_en_charge — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Date de prise en charge
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-03 ; 2025-01-04 ; 2025-01-05
   Format observé : AAAA-MM-JJ
- Date_théorique_prise_en_charge — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Date théorique de prise en charge
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-04 ; 2025-01-05 ; 2025-01-06
   Format observé : AAAA-MM-JJ
- Nombre_de_jour_prise_en_charge — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Jours écoulés pour la prise en charge
   Exemples : 2
   Valeurs observées (effectif) : 2 (300)
- Delai_prise_en_charge — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Délai de prise en charge
   Exemples : 2
   Valeurs observées (effectif) : 2 (300)
- Indicateur_retard_prise_en_charge — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Prise en charge en retard
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (300)
- Date_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Date de commande
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-05 ; 2025-01-06 ; 2025-01-07
   Format observé : AAAA-MM-JJ
- Date_theorique_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Date théorique de commande
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-05 ; 2025-01-06 ; 2025-01-07
   Format observé : AAAA-MM-JJ
- Nombre_de_jour_avant_commande — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Jours avant commande
   Exemples : 2
   Valeurs observées (effectif) : 2 (300)
- Delai_commande — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Délai de commande
   Exemples : 2
   Valeurs observées (effectif) : 2 (300)
- Indicateur_retard_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Commande en retard
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (300)
- Date_cloture — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 76.
   Description : Date de clôture
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2099-12-31 ; 2025-01-17 ; 2025-01-25
   Format observé : AAAA-MM-JJ
- Date_theorique_cloture — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 160.
   Description : Date théorique de clôture
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-15 ; 2025-01-17 ; 2025-01-19
   Format observé : AAAA-MM-JJ
- Nombre_de_jour_cloture — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 20.
   Description : Jours jusqu'à clôture
   Exemples : 14 ; 15 ; 16
   Plage observée : 14 à 33
- Delai_cloture — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 20.
   Description : Délai de clôture
   Exemples : 14 ; 15 ; 16
   Plage observée : 14 à 33
- Indicateur_retard_cloture — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Clôture en retard
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (300)
- Code_collaborateur_enregistrement — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Collaborateur ayant enregistré
   Format / valeurs indicatives : 3 lettres majuscules
   Exemples : C001 ; C002 ; C003
   Format observé : A999 (ex. C001)
- Code_collaborateur_suivi — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Collaborateur en charge du suivi
   Format / valeurs indicatives : 3 lettres majuscules
   Exemples : C002 ; C003 ; C004
   Format observé : A999 (ex. C002)
- Code_collaborateur_execution — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Collaborateur en charge de l'exécution
   Format / valeurs indicatives : 3 lettres majuscules
   Exemples : C003 ; C004 ; C005
   Format observé : A999 (ex. C003)
- Code_utilisateur_enregistrement — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Utilisateur ayant enregistré
   Exemples : USR00 ; USR01 ; USR02
   Format observé : AAA99 (ex. USR00)
- Code_utilisateur_suivi — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Utilisateur du suivi
   Exemples : USR01 ; USR02 ; USR03
   Format observé : AAA99 (ex. USR01)
- Code_utilisateur_execution — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Utilisateur de l'exécution
   Exemples : USR02 ; USR03 ; USR04
   Format observé : AAA99 (ex. USR02)
- Indicateur_validité_affectation — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Affectation valide
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (300)
- Libelle_niveau_reponse — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Niveau de réponse
   Format / valeurs indicatives : Niveau 1 / Niveau 2
   Exemples : Niveau 1
   Valeurs observées (effectif) : Niveau 1 (300)
- Lien_IKOS synthese_affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Lien vers la synthèse de l'affaire
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/affaire/AJ-608983 ; https://ikos.local/affaire/AC-608984 ; https://ikos.local/affaire/BSH-608985
- Lien_IKOS_liste_affaires_clients — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Lien vers la liste des affaires du client
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/client/AJ-003301 ; https://ikos.local/client/AC-003302 ; https://ikos.local/client/BSH-003303
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Affaire_pivot
Nombre de lignes : 300
- ID_Affaire — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Identifiant de l'affaire
   Format / valeurs indicatives : AC-608983
   Exemples : AJ-608983 ; AC-608984 ; BSH-608985
- ID_client_lot — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Identifiant client/lot
   Format / valeurs indicatives : Type_pivot-Code_societe-Code_client (CLT-AC-026905-LOT-AC-014311)
   Exemples : CLT-AJ-003301-LOT-AJ-000001 ; CLT-AC-003302-LOT-AC-000002 ; CLT-BSH-003303-LOT-BSH-000003
- Type_pivot — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Type de rattachement
   Format / valeurs indicatives : LOT / CLT-LOT / CLT
   Exemples : CLT-LOT
   Valeurs observées (effectif) : CLT-LOT (300)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Bail
Nombre de lignes : 400
- ID_bail — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Identifiant du bail
   Format / valeurs indicatives : Type_pivot-Code_societe-Code_client-Type_pivot-Code_societe-Code_lot-AAAA-MM-JJ
   Exemples : CLT-AJ-003301-LOT-AJ-000001-2018-01-01 ; CLT-AC-003302-LOT-AC-000002-2019-02-03 ; CLT-BSH-003303-LOT-BSH-000003-2020-03-05
- ID_client_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Identifiant client/lot
   Format / valeurs indicatives : CLT-AC-026905-LOT-AC-014311
   Exemples : CLT-AJ-003301-LOT-AJ-000001 ; CLT-AC-003302-LOT-AC-000002 ; CLT-BSH-003303-LOT-BSH-000003
- ID_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Client
   Format / valeurs indicatives : AC-003301
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (100) ; BSH (100) ; AJ (100) ; AC (100)
- Code_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Code client
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 003301 ; 003302 ; 003303
   Format observé : 999999 (ex. 003301)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Code lot
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Code_type_bail — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Code du type de bail
   Format / valeurs indicatives : 3 caractères (chiffres et lettres)
   Exemples : GLI ; BRS ; SOC
   Valeurs observées (effectif) : SOC (100) ; GLI (100) ; BRS (100) ; ANL (100)
- Libelle_type_bail — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Libellé du type de bail
   Format / valeurs indicatives : Antenne 9a Rnv 2an révANL / Bail Glissant / Bail Réel Solidaire / Com 3ans Rnv3ans RévANL…
   Exemples : Bail Glissant ; Bail Réel Solidaire ; Com 3ans Rnv3ans RévANL
   Valeurs observées (effectif) : Com 3ans Rnv3ans RévANL (100) ; Bail Réel Solidaire (100) ; Bail Glissant (100) ; Antenne 9a Rnv 2an révANL (100)
- Indicateur_lot_principal — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Lot principal ou secondaire
   Format / valeurs indicatives : Principale / Secondaire
   Exemples : Principale
   Valeurs observées (effectif) : Principale (400)
- Indicateur_lot_reference_rattachement_patrimoine — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Lot de référence pour le rattachement au patrimoine
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Indicateur_occupation_active — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Occupation en cours
   Format / valeurs indicatives : Actif / Inactif
   Exemples : Inactif ; Actif
   Valeurs observées (effectif) : Actif (320) ; Inactif (80)
- Date_debut_occupation_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Début d'occupation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2018-01-01 ; 2019-02-03 ; 2020-03-05
   Format observé : AAAA-MM-JJ
- Nombre_jours_depuis_debut_occupation_lot — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Jours depuis le début
   Exemples : 3202 ; 2804 ; 2408
   Plage observée : 287 à 3202
- Nombre_mois_depuis_debut_occupation_lot — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 24.
   Description : Mois depuis le début
   Exemples : 105 ; 92 ; 79
   Plage observée : 10 à 105
- Indicateur_nombre_mois_depuis_debut_occupation_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Indicateur d'ancienneté d'occupation (selon le PDF)
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Date_fin_occupation_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Fin d'occupation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-12-31 ; 2099-12-31
   Valeurs observées (effectif) : 2099-12-31 (320) ; 2025-12-31 (80)
- Nombre_jours_depuis_fin_occupation_lot — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Jours depuis la fin
   Exemples : 281 ; 0
   Valeurs observées (effectif) : 0 (320) ; 281 (80)
- Nombre_mois_depuis_fin_occupation_lot — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Mois depuis la fin
   Exemples : 10 ; 0
   Valeurs observées (effectif) : 0 (320) ; 10 (80)
- Indicateur_nombre_mois_depuis_fin_occupation_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Tranche de mois depuis la fin d'occupation
   Format / valeurs indicatives : 1 mois / 2 mois / 3 mois / 4 à 6 mois / 7 à 12 mois / 13 à 24 mois / 25 à 36 / 37 à 48 mois / 49 à 60 mois / > 60 mois
   Exemples : 4 à 6 mois ; 1 mois
   Valeurs observées (effectif) : 1 mois (320) ; 4 à 6 mois (80)
- Date_reception_preavis — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Réception du préavis
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-10-01 ; 2099-01-01
   Valeurs observées (effectif) : 2099-01-01 (320) ; 2025-10-01 (80)
- Nombre_jours_delais_prévis — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Nombre de jours de délai de préavis
   Exemples : 60
   Valeurs observées (effectif) : 60 (400)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Calendrier
Nombre de lignes : 731
- Date — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 731.
   Description : Jour
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-01 ; 2024-01-02 ; 2024-01-03
   Format observé : AAAA-MM-JJ
- Annee_mois — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 24.
   Description : Année-mois
   Format / valeurs indicatives : AAAA-MM
   Exemples : 2024-01-01 ; 2024-02-01 ; 2024-03-01
   Format observé : AAAA-MM-JJ
- Date_mois_debut — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 24.
   Description : Premier jour du mois
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-01 ; 2024-02-01 ; 2024-03-01
   Format observé : AAAA-MM-JJ
- Date_mois_fin — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 24.
   Description : Dernier jour du mois
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-31 ; 2024-02-29 ; 2024-03-31
   Format observé : AAAA-MM-JJ
- Annee — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 2.
   Description : Année
   Format / valeurs indicatives : AAAA
   Exemples : 2024-01-01 ; 2025-01-01
   Valeurs observées (effectif) : 2024-01-01 (366) ; 2025-01-01 (365)
- Date_annee_debut — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 2.
   Description : Premier jour de l'année
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-01 ; 2025-01-01
   Valeurs observées (effectif) : 2024-01-01 (366) ; 2025-01-01 (365)
- Date_annee_fin — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 2.
   Description : Dernier jour de l'année
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-12-31 ; 2025-12-31
   Valeurs observées (effectif) : 2024-12-31 (366) ; 2025-12-31 (365)
- Libelle_Mois — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 12.
   Description : Nom du mois
   Format / valeurs indicatives : janvier … décembre
   Exemples : janvier ; fevrier ; mars
   Valeurs observées (effectif) : octobre (62) ; mars (62) ; mai (62) ; juillet (62) ; janvier (62) ; decembre (62) ; aout (62) ; septembre (60) ; novembre (60) ; juin (60) ; avril (60) ; fevrier (57)
- Numero_Mois — Type SQLite : INTEGER. NULL observés : non (0/731). Valeurs distinctes non NULL : 12.
   Description : Numéro du mois
   Format / valeurs indicatives : 1 à 12
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 12 (62) ; 10 (62) ; 8 (62) ; 7 (62) ; 5 (62) ; 3 (62) ; 1 (62) ; 11 (60) ; 9 (60) ; 6 (60) ; 4 (60) ; 2 (57)
- Libelle_jour — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 7.
   Description : Nom du jour
   Format / valeurs indicatives : lundi … dimanche
   Exemples : lundi ; mardi ; mercredi
   Valeurs observées (effectif) : mercredi (105) ; mardi (105) ; lundi (105) ; vendredi (104) ; samedi (104) ; jeudi (104) ; dimanche (104)
- Numero_jour — Type SQLite : INTEGER. NULL observés : non (0/731). Valeurs distinctes non NULL : 31.
   Description : Jour du mois
   Format / valeurs indicatives : 1 à 31
   Exemples : 1 ; 2 ; 3
   Plage observée : 1 à 31
- Indicateur_jour_ouvre — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 2.
   Description : Jour ouvré
   Format / valeurs indicatives : Oui / Non
   Exemples : Non ; Oui
   Valeurs observées (effectif) : Oui (509) ; Non (222)
- Indicateur_jour_semaine — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 2.
   Description : Jour de semaine
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Oui (523) ; Non (208)
- Indicateur_jour_ferie — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 2.
   Description : Jour férié
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (715) ; Oui (16)
- Semestre — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 2.
   Description : Semestre
   Format / valeurs indicatives : S1 / S2
   Exemples : S1 ; S2
   Valeurs observées (effectif) : S2 (368) ; S1 (363)
- Date_semestre_debut — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 4.
   Description : Début du semestre
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-01 ; 2024-07-01 ; 2025-01-01
   Valeurs observées (effectif) : 2025-07-01 (184) ; 2024-07-01 (184) ; 2024-01-01 (182) ; 2025-01-01 (181)
- Date_semestre_fin — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 4.
   Description : Fin du semestre
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-06-30 ; 2024-12-31 ; 2025-06-30
   Valeurs observées (effectif) : 2025-12-31 (184) ; 2024-12-31 (184) ; 2024-06-30 (182) ; 2025-06-30 (181)
- Trimestre — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 4.
   Description : Trimestre
   Format / valeurs indicatives : T1 / T2 / T3 / T4
   Exemples : T1 ; T2 ; T3
   Valeurs observées (effectif) : T4 (184) ; T3 (184) ; T2 (182) ; T1 (181)
- Date_trimestre_debut — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 8.
   Description : Début du trimestre
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-01 ; 2024-04-01 ; 2024-07-01
   Valeurs observées (effectif) : 2025-10-01 (92) ; 2025-07-01 (92) ; 2024-10-01 (92) ; 2024-07-01 (92) ; 2025-04-01 (91) ; 2024-04-01 (91) ; 2024-01-01 (91) ; 2025-01-01 (90)
- Date_trimestre_fin — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 8.
   Description : Fin du trimestre
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-31 ; 2024-04-30 ; 2024-07-31
   Valeurs observées (effectif) : 2025-10-31 (92) ; 2025-07-31 (92) ; 2024-10-31 (92) ; 2024-07-31 (92) ; 2025-04-30 (91) ; 2024-04-30 (91) ; 2024-01-31 (91) ; 2025-01-31 (90)
- Numero_semaine_annee — Type SQLite : INTEGER. NULL observés : non (0/731). Valeurs distinctes non NULL : 52.
   Description : Semaine de l'année
   Format / valeurs indicatives : 1 à 53
   Exemples : 1 ; 2 ; 3
   Plage observée : 1 à 52
- Numero_jour_semaine — Type SQLite : INTEGER. NULL observés : non (0/731). Valeurs distinctes non NULL : 7.
   Description : Jour de la semaine
   Format / valeurs indicatives : 1 à 7
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 3 (105) ; 2 (105) ; 1 (105) ; 7 (104) ; 6 (104) ; 5 (104) ; 4 (104)
- Numero_jour_annee — Type SQLite : INTEGER. NULL observés : non (0/731). Valeurs distinctes non NULL : 366.
   Description : Jour de l'année
   Format / valeurs indicatives : 1 à 366
   Exemples : 1 ; 2 ; 3
   Plage observée : 1 à 366
- Numero_jour_calendrier — Type SQLite : INTEGER. NULL observés : non (0/731). Valeurs distinctes non NULL : 731.
   Description : Rang du jour dans le calendrier
   Format / valeurs indicatives : positif
   Exemples : 1 ; 2 ; 3
   Plage observée : 1 à 731
- Numero_jour_ouvre_calendrier — Type SQLite : INTEGER. NULL observés : non (0/731). Valeurs distinctes non NULL : 510.
   Description : Rang du jour ouvré dans le calendrier
   Format / valeurs indicatives : positif
   Exemples : 0 ; 1 ; 2
   Plage observée : 0 à 509
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/731). Valeurs distinctes non NULL : 731.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Client
Nombre de lignes : 400
- ID_client_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Identifiant client/lot
   Format / valeurs indicatives : CLT-AC-026905-LOT-AC-014311
   Exemples : CLT-AJ-003301-LOT-AJ-000001 ; CLT-AC-003302-LOT-AC-000002 ; CLT-BSH-003303-LOT-BSH-000003
- ID_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : ATTENTION : ID_client n'est PAS unique dans Client (320 clients distincts pour 400 lignes). Client est au grain client × lot (clé unique : ID_client_lot). Joindre une table enfant (Occupant, Client_historique…) sur ID_client vers Client multiplie les lignes ; utiliser COUNT(DISTINCT …) ou passer par Client_lot_pivot.
   Format / valeurs indicatives : AC-003301
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (100) ; BSH (100) ; AJ (100) ; AC (100)
- Code_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Code client
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 003301 ; 003302 ; 003303
   Format observé : 999999 (ex. 003301)
- Nom_prenom_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 16.
   Confidentialité : RGPD
   Description : Nom et prénom
   Format / valeurs indicatives : Suc MME CROCQ Odette, STE SCI PICARD…
   Exemples : MR MARTIN JEAN ; MME BERNARD MARIE ; MR DUBOIS LUCAS
   Valeurs observées (effectif) : MR SIMON THOMAS (25) ; MR ROBERT HUGO (25) ; MR PETIT LOUIS (25) ; MR MARTIN JEAN (25) ; MR LEROY PAUL (25) ; MR LEFEVRE NICOLAS (25) ; MR GARCIA ANTOINE (25) ; MR DUBOIS LUCAS (25) ; MME THOMAS EMMA (25) ; MME RICHARD CHLOE (25) ; MME MOREAU LEA (25) ; MME MICHEL SARAH (25) ; MME LAURENT JULIE (25) ; MME DURAND CAMILLE (25) ; MME DAVID MANON (25) ; MME BERNARD MARIE (25)
- Libelle_activite_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Activité du client
   Format / valeurs indicatives : Acquéreur, Commerce, Foyer, Locataire, Autre…
   Exemples : Locataire ; Foyer ; Commerce
   Valeurs observées (effectif) : Locataire (100) ; Foyer (100) ; Commerce (100) ; Acquéreur (100)
- Code_type_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Code du type de client
   Format / valeurs indicatives : ACQ / BRS / CLT / COM / CVM / FAI / FOY / LAC / LAQ / PRO / PSL / SDN / VHL
   Exemples : CLT ; FOY ; COM
   Valeurs observées (effectif) : FOY (100) ; COM (100) ; CLT (100) ; ACQ (100)
- Libelle_type_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Libellé du type de client
   Format / valeurs indicatives : Acquéreur Promotion / Acquéreur PSLA / Acquéreur vente HLM / Client acquéreur / Client locataire / Client Locataire BRS / Client vente mandat / Commercial ou professio. / Copropriétaire / Facturation interne / Foyers / Locataire-Acquéreur / Sans Droit ni titre
   Exemples : Client locataire ; Foyers ; Commercial ou professionnel
   Valeurs observées (effectif) : Foyers (100) ; Commercial ou professionnel (100) ; Client locataire (100) ; Client acquéreur (100)
- Code_categorie_menage — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Description : Catégorie de ménage
   Format / valeurs indicatives : I0 / IM1 … IM9 / M0
   Exemples : I0 ; IM1 ; IM2
   Valeurs observées (effectif) : M0 (80) ; IM3 (80) ; IM2 (80) ; IM1 (80) ; I0 (80)
- Libelle_composition_familiale — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Confidentialité : RGPD
   Description : Composition familiale
   Format / valeurs indicatives : Autre / Couple avec enfant / Couple sans enfant / Monoparentale / Personne seule
   Exemples : Personne seule ; Couple sans enfant ; Couple avec enfant
   Valeurs observées (effectif) : Personne seule (80) ; Monoparentale (80) ; Couple sans enfant (80) ; Couple avec enfant (80) ; Autre (80)
- Nombre_occupant_enfant — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Nombre d'enfants
   Exemples : 0 ; 1 ; 2
   Valeurs observées (effectif) : 0 (134) ; 2 (133) ; 1 (133)
- Nombre_occupant_adulte — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Nombre d'adultes
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 1 (134) ; 3 (133) ; 2 (133)
- Nombre_occupant_autre — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Confidentialité : RGPD
   Description : Autres occupants
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (200) ; 0 (200)
- Nombre_occupant_personne — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 6.
   Confidentialité : RGPD
   Description : Total d'occupants
   Exemples : 1 ; 4 ; 5
   Valeurs observées (effectif) : 5 (67) ; 4 (67) ; 2 (67) ; 1 (67) ; 6 (66) ; 3 (66)
- Date_debut_occupation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Début d'occupation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2018-01-01 ; 2019-02-03 ; 2020-03-05
   Format observé : AAAA-MM-JJ
- Date_fin_occupation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Description : Fin d'occupation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-12-31 ; 2025-01-02 ; 2025-01-03
   Format observé : AAAA-MM-JJ
- Indicateur_statut_presence — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Statut de présence
   Format / valeurs indicatives : Présent / Parti
   Exemples : Parti ; Présent
   Valeurs observées (effectif) : Présent (320) ; Parti (80)
- Annee_revenus_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Année de référence des revenus
   Format / valeurs indicatives : AAAA
   Exemples : 2025-01-01
   Valeurs observées (effectif) : 2025-01-01 (400)
- Montant_revenus_client — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 20.
   Confidentialité : RGPD
   Description : Revenus du client
   Exemples : 18000 ; 19200 ; 20400
   Plage observée : 18000 à 40800
- Montant_plafond_plus — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Description : Plafond de ressources PLUS
   Exemples : 24000 ; 25000 ; 26000
   Valeurs observées (effectif) : 28000 (80) ; 27000 (80) ; 26000 (80) ; 25000 (80) ; 24000 (80)
- Pourcentage_revenus_plafond_plus — Type SQLite : REAL. NULL observés : non (0/400). Valeurs distinctes non NULL : 20.
   Confidentialité : RGPD
   Description : Revenus / plafond PLUS
   Format / valeurs indicatives : 0 à 1
   Exemples : 0.75 ; 0.768 ; 0.785
   Plage observée : 0.75 à 1.5
- Classe_pourcentage_revenus_plafond_plus — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 7.
   Confidentialité : RGPD
   Description : Tranche du ratio revenus/plafond
   Format / valeurs indicatives : 20% et moins / 20%-40% / 40%-60% / 60%-80% / 80%-100% / 100%-120% / 120% et plus
   Exemples : 20% et moins ; 20%-40% ; 40%-60%
   Valeurs observées (effectif) : 20% et moins (58) ; 80%-100% (57) ; 60%-80% (57) ; 40%-60% (57) ; 20%-40% (57) ; 120% et plus (57) ; 100%-120% (57)
- Code_departement_adresse_temporaire — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Confidentialité : RGPD
   Description : Département de l'adresse temporaire
   Format / valeurs indicatives : 1 à 976
   Exemples : 35 ; 36 ; 37
   Valeurs observées (effectif) : 39 (80) ; 38 (80) ; 37 (80) ; 36 (80) ; 35 (80)
- Code_commune_adresse_temporaire — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 100.
   Confidentialité : RGPD
   Description : Commune (code)
   Format / valeurs indicatives : 5 chiffres
   Exemples : 35000 ; 35001 ; 35002
   Plage observée : 35000 à 35099
- Code_postal_adresse_temporaire — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 100.
   Confidentialité : RGPD
   Description : Code postal
   Format / valeurs indicatives : 5 chiffres (35160)
   Exemples : 35000 ; 35001 ; 35002
   Plage observée : 35000 à 35099
- Libelle_commune_adresse_temporaire — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Confidentialité : RGPD
   Description : Commune
   Format / valeurs indicatives : RENNES / GUERANDE / SAINT-MALO…
   Exemples : RENNES ; GUERANDE ; SAINT-MALO
   Valeurs observées (effectif) : VANNES (80) ; SAINT-MALO (80) ; RENNES (80) ; LORIENT (80) ; GUERANDE (80)
- Libelle_numero_rue_adresse_temporaire — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Numéro et rue
   Format / valeurs indicatives : 9 RUE BOURGALIN
   Exemples : 1 RUE BOURGALIN ; 2 RUE BOURGALIN ; 3 RUE BOURGALIN
- Nom_prenom_CSR_referent — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 16.
   Confidentialité : RGPD
   Description : CSR référent
   Format / valeurs indicatives : Prénom NOM
   Exemples : CSR Jean Martin ; CSR Marie Bernard ; CSR Lucas Dubois
   Valeurs observées (effectif) : CSR Thomas Simon (25) ; CSR Sarah Michel (25) ; CSR Paul Leroy (25) ; CSR Nicolas Lefevre (25) ; CSR Marie Bernard (25) ; CSR Manon David (25) ; CSR Lucas Dubois (25) ; CSR Louis Petit (25) ; CSR Lea Moreau (25) ; CSR Julie Laurent (25) ; CSR Jean Martin (25) ; CSR Hugo Robert (25) ; CSR Emma Thomas (25) ; CSR Chloe Richard (25) ; CSR Camille Durand (25) ; CSR Antoine Garcia (25)
- Lien_IKOS_synthese_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Lien vers la synthèse client
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/client/AJ-003301 ; https://ikos.local/client/AC-003302 ; https://ikos.local/client/BSH-003303
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Client_historique
Nombre de lignes : 900
- ID_client — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Client
   Format / valeurs indicatives : AC-003301
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- ID_client_annee_mois — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 900.
   Confidentialité : RGPD
   Description : Client et mois
   Format / valeurs indicatives : Code_societe-Code_client-AAAA-MM
   Exemples : AJ-003301-2025-01 ; AC-003302-2025-01 ; BSH-003303-2025-01
- Annee_mois — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 3.
   Description : Mois de la photo
   Format / valeurs indicatives : AAAA-MM
   Exemples : 2025-01-01 ; 2025-02-01 ; 2025-03-01
   Valeurs observées (effectif) : 2025-02-01 (320) ; 2025-01-01 (320) ; 2025-03-01 (260)
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (225) ; BSH (225) ; AJ (225) ; AC (225)
- Code_client — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Code client
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 003301 ; 003302 ; 003303
   Format observé : 999999 (ex. 003301)
- Nom_prenom_client — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 16.
   Confidentialité : RGPD
   Description : Nom et prénom
   Format / valeurs indicatives : MR GOULAY NORBERT
   Exemples : MR MARTIN JEAN ; MME BERNARD MARIE ; MR DUBOIS LUCAS
   Valeurs observées (effectif) : MR MARTIN JEAN (57) ; MR DUBOIS LUCAS (57) ; MME THOMAS EMMA (57) ; MME BERNARD MARIE (57) ; MR SIMON THOMAS (56) ; MR ROBERT HUGO (56) ; MR PETIT LOUIS (56) ; MR LEROY PAUL (56) ; MR LEFEVRE NICOLAS (56) ; MR GARCIA ANTOINE (56) ; MME RICHARD CHLOE (56) ; MME MOREAU LEA (56) ; MME MICHEL SARAH (56) ; MME LAURENT JULIE (56) ; MME DURAND CAMILLE (56) ; MME DAVID MANON (56)
- Indicateur_statut_presence — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Client présent
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Oui (788) ; Non (112)
- Date_debut_occupation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 320.
   Description : Début d'occupation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2018-01-01 ; 2019-02-03 ; 2020-03-05
   Format observé : AAAA-MM-JJ
- Date_fin_occupation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Fin d'occupation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-12-31 ; 2099-12-31
   Valeurs observées (effectif) : 2099-12-31 (720) ; 2025-12-31 (180)
- Nombre_jours_depuis_debut_occupation — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 776.
   Description : Jours depuis le début
   Exemples : 2557 ; 2159 ; 1763
   Plage observée : 0 à 2616
- Nombre_mois_depuis_debut_occupation — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 62.
   Description : Mois depuis le début
   Exemples : 84 ; 71 ; 58
   Plage observée : 0 à 86
- Indicateur_nombre_mois_depuis_debut_occupation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Indicateur d'ancienneté (début)
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (900)
- Nombre_jours_depuis_fin_occupation — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Jours depuis la fin
   Exemples : 0
   Valeurs observées (effectif) : 0 (900)
- Nombre_mois_depuis_fin_occupation — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Mois depuis la fin
   Exemples : 0
   Valeurs observées (effectif) : 0 (900)
- Indicateur_nombre_mois_depuis_fin_occupation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Indicateur d'ancienneté (fin)
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (720) ; Oui (180)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 731.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Client_lot_pivot
Nombre de lignes : 400
- ID_client_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Identifiant client/lot
   Format / valeurs indicatives : CLT-AC-026905-LOT-AC-014311
   Exemples : CLT-AJ-003301-LOT-AJ-000001 ; CLT-AC-003302-LOT-AC-000002 ; CLT-BSH-003303-LOT-BSH-000003
- ID_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Client
   Format / valeurs indicatives : AC-003301
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- Type_pivot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Type de rattachement
   Format / valeurs indicatives : LOT / CLT-LOT / CLT
   Exemples : CLT-LOT
   Valeurs observées (effectif) : CLT-LOT (400)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Collaborateur
Nombre de lignes : 30
- ID_organisation — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Description : Organisation de rattachement
   Format / valeurs indicatives : AC-R2-01-08
   Exemples : AJ-R1-01-01 ; AC-R2-02-02 ; BSH-R3-03-03
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : AJ (8) ; AC (8) ; MF1 (7) ; BSH (7)
- Code_niveau_organisation_1 — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 8.
   Description : Organisation niveau 1
   Format / valeurs indicatives : 2 à 4 caractères
   Exemples : R1 ; R2 ; R3
   Valeurs observées (effectif) : R6 (4) ; R5 (4) ; R4 (4) ; R3 (4) ; R2 (4) ; R1 (4) ; R8 (3) ; R7 (3)
- Code_niveau_organisation_2 — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 9.
   Description : Organisation niveau 2
   Format / valeurs indicatives : 01 / 02 / 03 / 04 / 05 / 09 / BR
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 03 (4) ; 02 (4) ; 01 (4) ; 09 (3) ; 08 (3) ; 07 (3) ; 06 (3) ; 05 (3) ; 04 (3)
- Code_niveau_organisation_3 — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 12.
   Description : Organisation niveau 3
   Format / valeurs indicatives : 01 / 02 / 03 / 04 / 05 / 06 / 07 / 08 / 09 / 11 / 12
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 06 (3) ; 05 (3) ; 04 (3) ; 03 (3) ; 02 (3) ; 01 (3) ; 12 (2) ; 11 (2) ; 10 (2) ; 09 (2) ; 08 (2) ; 07 (2)
- Code_collaborateur — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Identifiant du collaborateur
   Format / valeurs indicatives : MTOUTIRAIS / MTRUONG
   Exemples : C001 ; C002 ; C003
   Format observé : A999 (ex. C001)
- Nom_prenom_collaborateur — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 16.
   Confidentialité : RGPD
   Description : Nom et prénom
   Format / valeurs indicatives : Mathilde TOUTIRAIS
   Exemples : Jean Martin ; Marie Bernard ; Lucas Dubois
   Valeurs observées (effectif) : Thomas Simon (2) ; Sarah Michel (2) ; Paul Leroy (2) ; Nicolas Lefevre (2) ; Marie Bernard (2) ; Lucas Dubois (2) ; Louis Petit (2) ; Lea Moreau (2) ; Julie Laurent (2) ; Jean Martin (2) ; Hugo Robert (2) ; Emma Thomas (2) ; Chloe Richard (2) ; Camille Durand (2) ; Manon David (1) ; Antoine Garcia (1)
- Mail_collaborateur — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Adresse e-mail
   Format / valeurs indicatives : xxxxxx@aiguillon.com
   Exemples : collab1@aiguillon.local ; collab2@aiguillon.local ; collab3@aiguillon.local
- Code_fonction — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 3.
   Description : Code de la fonction
   Format / valeurs indicatives : 2 ou 3 lettres majuscules
   Exemples : GL ; CD ; CC
   Valeurs observées (effectif) : GL (10) ; CD (10) ; CC (10)
- Libelle_fonction — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 3.
   Description : Libellé de la fonction
   Format / valeurs indicatives : Gestionnaire Loyer / Chargé développement / Chargé de contentieux…
   Exemples : Gestionnaire Loyer ; Chargé développement ; Chargé de contentieux
   Valeurs observées (effectif) : Gestionnaire Loyer (10) ; Chargé développement (10) ; Chargé de contentieux (10)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Commande
Nombre de lignes : 300
- ID_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Identifiant
   Format / valeurs indicatives : Code_societe-Numero_commande (AC-011065)
   Exemples : AJ-011065 ; AC-011066 ; BSH-011067
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (75) ; BSH (75) ; AJ (75) ; AC (75)
- Numero_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Numéro de commande
   Format / valeurs indicatives : 6 chiffres
   Exemples : 011065 ; 011066 ; 011067
   Format observé : 999999 (ex. 011065)
- ID_organisation — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Description : Organisation
   Format / valeurs indicatives : AC-R2-01-08
   Exemples : AJ-R1-01-01 ; AC-R2-02-02 ; BSH-R3-03-03
- Code_niveau_organisation_1 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 8.
   Description : Organisation niveau 1
   Format / valeurs indicatives : 2 à 4 caractères
   Exemples : R1 ; R2 ; R3
   Valeurs observées (effectif) : R6 (40) ; R5 (40) ; R4 (40) ; R3 (40) ; R2 (40) ; R1 (40) ; R8 (30) ; R7 (30)
- Code_niveau_organisation_2 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 9.
   Description : Organisation niveau 2
   Format / valeurs indicatives : 01 / 02 / 03 / 04 / 05 / 09 / BR
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 03 (40) ; 02 (40) ; 01 (40) ; 09 (30) ; 08 (30) ; 07 (30) ; 06 (30) ; 05 (30) ; 04 (30)
- Code_niveau_organisation_3 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 12.
   Description : Organisation niveau 3
   Format / valeurs indicatives : 01 … 09 / 11 / 12
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 06 (30) ; 05 (30) ; 04 (30) ; 03 (30) ; 02 (30) ; 01 (30) ; 12 (20) ; 11 (20) ; 10 (20) ; 09 (20) ; 08 (20) ; 07 (20)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 80.
   Description : Patrimoine niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 9.
   Description : Patrimoine niveau 2
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 06 (34) ; 05 (34) ; 04 (34) ; 03 (34) ; 02 (34) ; 01 (34) ; 08 (33) ; 07 (33) ; 09 (30)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 12.
   Description : Patrimoine niveau 3
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (26) ; 07 (26) ; 06 (26) ; 05 (26) ; 04 (26) ; 03 (26) ; 02 (26) ; 01 (26) ; 12 (23) ; 11 (23) ; 10 (23) ; 09 (23)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Lot concerné
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Type_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 3.
   Description : Code du type de commande
   Format / valeurs indicatives : 3 lettres majuscules
   Exemples : FOY ; COM ; INF
   Valeurs observées (effectif) : INF (100) ; FOY (100) ; COM (100)
- Libelle_type_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 3.
   Description : Libellé du type
   Format / valeurs indicatives : Cde Foyers Mandat GOP / Cde Mandat commercial / Cde Informatique
   Exemples : Cde Foyers Mandat GOP ; Cde Mandat commercial ; Cde Informatique
   Valeurs observées (effectif) : Cde Mandat commercial (100) ; Cde Informatique (100) ; Cde Foyers Mandat GOP (100)
- Libelle_objet_commande_1 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Objet (ligne 1)
   Format / valeurs indicatives : cellule ascenseur HS
   Exemples : cellule ascenseur HS ; Remplacement robinet ; Controle VMC
   Valeurs observées (effectif) : cellule ascenseur HS (100) ; Remplacement robinet (100) ; Controle VMC (100)
- Libelle_objet_commande_2 — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Objet (ligne 2)
   Exemples : Intervention technique
   Valeurs observées (effectif) : Intervention technique (300)
- Commentaire_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Commentaire
   Format / valeurs indicatives : Une intervention est programmée le 30/10
   Exemples : Une intervention est programmee le 30/10
   Valeurs observées (effectif) : Une intervention est programmee le 30/10 (300)
- Montant_HT — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 100.
   Description : Montant HT
   Exemples : 500 ; 535 ; 570
   Plage observée : 500 à 3965
- Montant_TVA — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 100.
   Description : Montant de TVA
   Exemples : 100 ; 107 ; 114
   Plage observée : 100 à 793
- Montant_TTC — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 100.
   Description : Montant TTC
   Exemples : 600 ; 642 ; 684
   Plage observée : 600 à 4758
- Code_tiers — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Code du fournisseur
   Format / valeurs indicatives : 9 chiffres
   Exemples : 400000000 ; 400000001 ; 400000002
   Format observé : 999999999 (ex. 400000000)
- Libelle_tiers — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 2.
   Confidentialité : RGPD
   Description : Nom du fournisseur
   Format / valeurs indicatives : ARMOR EVASION / HOMIWOO
   Exemples : ARMOR EVASION ; HOMIWOO
   Valeurs observées (effectif) : HOMIWOO (150) ; ARMOR EVASION (150)
- Telephone_fixe_tiers — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Téléphone fixe
   Format / valeurs indicatives : 10 chiffres
   Exemples : 0299000000 ; 0299000001 ; 0299000002
- Telephone_portable_tiers — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Téléphone portable
   Format / valeurs indicatives : 10 chiffres
   Exemples : 0699000000 ; 0699000001 ; 0699000002
- Mail_tiers — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : E-mail du tiers
   Format / valeurs indicatives : sav@lepage-electronique.com
   Exemples : sav.fournisseur0@local.test ; sav.fournisseur1@local.test ; sav.fournisseur2@local.test
- Code_collaborateur_executant_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Collaborateur exécutant
   Format / valeurs indicatives : 2 ou 3 caractères (lettres majuscules et chiffres)
   Exemples : C001 ; C002 ; C003
   Format observé : A999 (ex. C001)
- Code_utilisateur_executant_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Utilisateur exécutant (type non précisé dans le PDF)
   Exemples : USR000 ; USR001 ; USR002
   Format observé : AAA999 (ex. USR000)
- Date_enregistrement_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Enregistrement
   Exemples : 2025-01-01 00:00:00.000 ; 2025-01-02 01:07:13.000 ; 2025-01-03 02:14:26.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Date_signature_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Signature
   Exemples : 2025-01-03 00:00:00.000 ; 2025-01-04 01:07:13.000 ; 2025-01-05 02:14:26.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Date_debut_execution_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Début d'exécution
   Exemples : 2025-01-06 00:00:00.000 ; 2025-01-07 01:07:13.000 ; 2025-01-08 02:14:26.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Date_fin_execution_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Fin d'exécution
   Exemples : 2025-01-16 00:00:00.000 ; 2025-01-18 01:07:13.000 ; 2025-01-20 02:14:26.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Nombre_jours_depuis_commande — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Jours depuis la commande
   Exemples : 645 ; 644 ; 643
   Plage observée : 346 à 645
- Indicateur_categorie_delai_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 1.
   Description : Catégorie de délai
   Format / valeurs indicatives : Inférieur ou égal à 30 jours / Supérieur à 30 jours
   Exemples : Inférieur ou égal à 30 jours
   Valeurs observées (effectif) : Inférieur ou égal à 30 jours (300)
- Taux_execution_commande — Type SQLite : INTEGER. NULL observés : non (0/300). Valeurs distinctes non NULL : 2.
   Description : Taux d'exécution (%)
   Format / valeurs indicatives : 0 à 100
   Exemples : 50 ; 100
   Valeurs observées (effectif) : 100 (240) ; 50 (60)
- Libelle_etat_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 3.
   Description : État de la commande
   Format / valeurs indicatives : Partiellement soldée / Enregistrement / Non soldée / En cours / NULL
   Exemples : En cours ; Partiellement soldée ; Non soldée
   Valeurs observées (effectif) : Partiellement soldée (100) ; Non soldée (100) ; En cours (100)
- Indicateur_charge_a_payer — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 2.
   Description : Charge à payer
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (225) ; Oui (75)
- Statut_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 4.
   Description : Code du statut
   Format / valeurs indicatives : TRX / ANN / ENR / MOD / SLD / BON
   Exemples : TRX ; ENR ; SLD
   Valeurs observées (effectif) : TRX (75) ; SLD (75) ; ENR (75) ; BON (75)
- Libelle_statut_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 4.
   Description : Libellé du statut
   Format / valeurs indicatives : Annulée / Bon commande édité / Enregistrée / Modifiée / Exécutée / Soldée / NULL
   Exemples : Exécutée ; Enregistrée ; Soldée
   Valeurs observées (effectif) : Soldée (75) ; Exécutée (75) ; Enregistrée (75) ; Bon commande édité (75)
- Lien_IKOS_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Confidentialité : RGPD
   Description : Lien IKOS
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/commande/AJ-011065 ; https://ikos.local/commande/AC-011066 ; https://ikos.local/commande/BSH-011067
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Commande_lot_pivot
Nombre de lignes : 300
- ID_commande — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Commande
   Format / valeurs indicatives : AC-011065
   Exemples : AJ-011065 ; AC-011066 ; BSH-011067
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/300). Valeurs distinctes non NULL : 300.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Contentieux_client_historique
Nombre de lignes : 400
- ID_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Client
   Format / valeurs indicatives : AC-003301
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- ID_client_annee_mois — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Client et mois
   Format / valeurs indicatives : AC-064528-2024-06
   Exemples : AJ-003301-2025-01 ; AC-003302-2025-01 ; BSH-003303-2025-01
- Annee_mois — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Mois
   Format / valeurs indicatives : AAAA-MM
   Exemples : 2025-01-01 ; 2025-02-01
   Valeurs observées (effectif) : 2025-01-01 (320) ; 2025-02-01 (80)
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (100) ; BSH (100) ; AJ (100) ; AC (100)
- Code_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Code client
   Format / valeurs indicatives : Nombre à 6 chiffres
   Exemples : 003301 ; 003302 ; 003303
   Format observé : 999999 (ex. 003301)
- Libelle_procedure — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : Procédure en cours
   Format / valeurs indicatives : Assignation / Surendettement…
   Exemples : Assignation ; Surendettement ; Enquete
   Valeurs observées (effectif) : Assignation (134) ; Surendettement (133) ; Enquete (133)
- Libelle_etape_procedure — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : Étape de la procédure
   Exemples : Ouverture ; Instruction ; Cloture
   Valeurs observées (effectif) : Ouverture (134) ; Instruction (133) ; Cloture (133)
- Date_debut_procedure — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Début
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-01 ; 2024-01-02 ; 2024-01-03
   Format observé : AAAA-MM-JJ
- Date_fin_procedure — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Fin
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-03-31 ; 2024-04-01 ; 2024-04-02
   Format observé : AAAA-MM-JJ
- Libelle_procedure_cumulable — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Procédure cumulable
   Format / valeurs indicatives : Enquête / Aide financière…
   Exemples : Enquete ; Aide financiere
   Valeurs observées (effectif) : Enquete (200) ; Aide financiere (200)
- Indicateur_dossier_titre — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Dossier avec titre exécutoire
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (300) ; Oui (100)
- Date_prescription — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Date de prescription
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2027-01-01
   Valeurs observées (effectif) : 2027-01-01 (400)
- Nombre_jour_delai_prescription — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 100.
   Description : Jours avant prescription
   Exemples : 450 ; 449 ; 448
   Plage observée : 351 à 450
- Classe_nombre_jour_delai_prescription — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Tranche de délai
   Format / valeurs indicatives : Prescrit / 0-1 an / 1-2 ans / 2-3 ans / 3 ans et plus
   Exemples : 0-1 an ; 1-2 ans ; 2-3 ans
   Valeurs observées (effectif) : 3 ans et plus (100) ; 2-3 ans (100) ; 1-2 ans (100) ; 0-1 an (100)
- Indicateur_depassement_delais_prescription — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Délai dépassé
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Indicateur_procedure_surendettement_active — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Surendettement actif
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (266) ; Oui (134)
- Indicateur_procedure_enquete_active — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Enquête active
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (300) ; Oui (100)
- Indicateur_procedure_saisie_active — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Saisie active
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Indicateur_procedure_plan_active — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Plan actif
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (320) ; Oui (80)
- Indicateur_procedure_capex_active — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Procédure CAPEX active
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Indicateur_plan_PRP — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Plan PRP
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (333) ; Oui (67)
- Raison_sociale_huissier_referent — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 20.
   Description : Huissier référent
   Exemples : Huissier 01 ; Huissier 02 ; Huissier 03
- Indicateur_check_mois_en_cours — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Contrôle mois en cours
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Indicateur_check_sortie — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Contrôle de sortie
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Copropriete
Nombre de lignes : 80
- ID_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Copropriété
   Format / valeurs indicatives : Code_societe-Code_niveau_patrimoine_1[-2[-3]]-Type_copropriete (AC-BBO-ST-COPRO)
   Exemples : AJ-COP-00001 ; AC-COP-00002 ; BSH-COP-00003
- ID_copropriete_document_source — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Copropriété + document source
   Format / valeurs indicatives : …-Type_document_source-Type_copropriete (AC-PNRK-02-PV-20250204-COPRO)
   Exemples : AJ-COP-00001-DOC-001 ; AC-COP-00002-DOC-001 ; BSH-COP-00003-DOC-001
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Patrimoine
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (20) ; BSH (20) ; AJ (20) ; AC (20)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Patrimoine niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 9.
   Description : Patrimoine niveau 2
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (9) ; 07 (9) ; 06 (9) ; 05 (9) ; 04 (9) ; 03 (9) ; 02 (9) ; 01 (9) ; 09 (8)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 12.
   Description : Patrimoine niveau 3
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (7) ; 07 (7) ; 06 (7) ; 05 (7) ; 04 (7) ; 03 (7) ; 02 (7) ; 01 (7) ; 12 (6) ; 11 (6) ; 10 (6) ; 09 (6)
- Date_document_source — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 1.
   Description : Date du document
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-06-01
   Valeurs observées (effectif) : 2025-06-01 (80)
- Type_document_source — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 1.
   Description : Type de document
   Format / valeurs indicatives : AG / PV
   Exemples : PV
   Valeurs observées (effectif) : PV (80)
- Type_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 4.
   Description : Type de copropriété
   Format / valeurs indicatives : AFUL / ASL / COPRO / UNION
   Exemples : COPRO ; ASL ; AFUL
   Valeurs observées (effectif) : UNION (20) ; COPRO (20) ; ASL (20) ; AFUL (20)
- ID_immatriculation_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Numéro d'immatriculation
   Format / valeurs indicatives : 2 lettres majuscules + 7 chiffres
   Exemples : IMM00000001 ; IMM00000002 ; IMM00000003
   Format observé : AAA99999999 (ex. IMM00000001)
- Nom_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Nom
   Format / valeurs indicatives : ASL DU HAMEAU DE KERBIHAN
   Exemples : Copropriete 001 ; Copropriete 002 ; Copropriete 003
- Date_immatriculation_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 8.
   Description : Immatriculation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2018-01-01 ; 2019-01-01 ; 2020-01-01
   Valeurs observées (effectif) : 2025-01-01 (10) ; 2024-01-01 (10) ; 2023-01-01 (10) ; 2022-01-01 (10) ; 2021-01-01 (10) ; 2020-01-01 (10) ; 2019-01-01 (10) ; 2018-01-01 (10)
- Date_reglement_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 7.
   Description : Règlement de copropriété
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2019-05-01 ; 2020-05-01 ; 2021-05-01
   Valeurs observées (effectif) : 2021-05-01 (12) ; 2020-05-01 (12) ; 2019-05-01 (12) ; 2025-05-01 (11) ; 2024-05-01 (11) ; 2023-05-01 (11) ; 2022-05-01 (11)
- Adresse_complete_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Adresse complète
   Format / valeurs indicatives : 4 Rue des epinettes 44115 Haute-Goulaine
   Exemples : 20 RUE DU PORT ; 21 RUE DU PORT ; 22 RUE DU PORT
- Adresse_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Adresse (rue)
   Format / valeurs indicatives : 18 BIS rue de Rennes
   Exemples : 20 RUE DU PORT ; 21 RUE DU PORT ; 22 RUE DU PORT
- Code_postal_copropriete — Type SQLite : INTEGER. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Code postal
   Format / valeurs indicatives : 5 chiffres
   Exemples : 35000 ; 35001 ; 35002
   Plage observée : 35000 à 35079
- Libelle_commune_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 5.
   Description : Commune
   Format / valeurs indicatives : Rennes
   Exemples : RENNES ; NANTES ; BREST
   Valeurs observées (effectif) : VANNES (16) ; RENNES (16) ; NANTES (16) ; LORIENT (16) ; BREST (16)
- ID_syndic — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Identifiant du syndic
   Format / valeurs indicatives : 16 chiffres (48753009900024)
   Exemples : SYND-00001 ; SYND-00002 ; SYND-00003
   Format observé : AAAA-99999 (ex. SYND-00001)
- Nom_syndic — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Nom du syndic
   Format / valeurs indicatives : BREIZH COMMERCES
   Exemples : Syndic 001 ; Syndic 002 ; Syndic 003
- Adresse_complete_syndic — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Adresse complète du syndic
   Exemples : 5 RUE DU SYNDIC ; 6 RUE DU SYNDIC ; 7 RUE DU SYNDIC
- Adresse_syndic — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Adresse (rue) du syndic
   Exemples : 5 RUE DU SYNDIC ; 6 RUE DU SYNDIC ; 7 RUE DU SYNDIC
- Code_postal_syndic — Type SQLite : INTEGER. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Code postal du syndic
   Format / valeurs indicatives : 5 chiffres
   Exemples : 35000 ; 35001 ; 35002
   Plage observée : 35000 à 35079
- Libelle_commune_syndic — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 5.
   Description : Commune du syndic (type non précisé)
   Exemples : RENNES ; NANTES ; BREST
   Valeurs observées (effectif) : VANNES (16) ; RENNES (16) ; NANTES (16) ; LORIENT (16) ; BREST (16)
- Tel_syndic — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Téléphone
   Format / valeurs indicatives : 10 chiffres
   Exemples : 0299000000 ; 0299000001 ; 0299000002
- Mail_syndic — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : E-mail
   Exemples : syndic1@local.test ; syndic2@local.test ; syndic3@local.test
- Etat_mandat_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 3.
   Description : État du mandat
   Format / valeurs indicatives : Pas de mandat en cours / Mandat en cours / Mandat expiré sans successeur déclaré / NULL
   Exemples : Pas de mandat en cours ; Mandat en cours ; Mandat expiré sans successeur déclaré
   Valeurs observées (effectif) : Pas de mandat en cours (27) ; Mandat en cours (27) ; Mandat expiré sans successeur déclaré (26)
- Date_fin_mandat_copropriete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 1.
   Description : Fin du mandat
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2027-12-31
   Valeurs observées (effectif) : 2027-12-31 (80)
- Tantiemes_aiguillon — Type SQLite : INTEGER. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Tantièmes détenus
   Exemples : 50 ; 51 ; 52
   Plage observée : 50 à 129
- Total_tantiemes_copropriete — Type SQLite : INTEGER. NULL observés : non (0/80). Valeurs distinctes non NULL : 1.
   Description : Total des tantièmes
   Exemples : 1000
   Valeurs observées (effectif) : 1000 (80)
- Date_integration — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Intégration
   Exemples : 2025-01-01 00:00:00.000 ; 2025-01-02 01:07:13.000 ; 2025-01-03 02:14:26.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Date_validation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Validation
   Exemples : 2025-01-02 01:07:13.000 ; 2025-01-03 02:14:26.000 ; 2025-01-04 03:21:39.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Copropriete_resolution
Nombre de lignes : 160
- ID_copropriete — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 80.
   Description : Copropriété
   Format / valeurs indicatives : AC-BBO-ST-COPRO
   Exemples : AJ-COP-00001 ; AC-COP-00002 ; BSH-COP-00003
- ID_copropriete_document_source — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 80.
   Description : Copropriété + document
   Format / valeurs indicatives : AC-PNRK-02-PV-20250204-COPRO
   Exemples : AJ-COP-00001-DOC-001 ; AC-COP-00002-DOC-001 ; BSH-COP-00003-DOC-001
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 80.
   Description : Patrimoine
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (40) ; BSH (40) ; AJ (40) ; AC (40)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 80.
   Description : Patrimoine niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 9.
   Description : Patrimoine niveau 2
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (18) ; 07 (18) ; 06 (18) ; 05 (18) ; 04 (18) ; 03 (18) ; 02 (18) ; 01 (18) ; 09 (16)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 12.
   Description : Patrimoine niveau 3
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (14) ; 07 (14) ; 06 (14) ; 05 (14) ; 04 (14) ; 03 (14) ; 02 (14) ; 01 (14) ; 12 (12) ; 11 (12) ; 10 (12) ; 09 (12)
- Date_document_source — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 1.
   Description : Date du document
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-06-01
   Valeurs observées (effectif) : 2025-06-01 (160)
- Type_document_source — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 1.
   Description : Type de document
   Format / valeurs indicatives : PV / AG
   Exemples : PV
   Valeurs observées (effectif) : PV (160)
- Type_copropriete — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 4.
   Description : Type de copropriété
   Format / valeurs indicatives : COPRO / ASL / AFUL / UNION
   Exemples : COPRO ; ASL ; AFUL
   Valeurs observées (effectif) : UNION (40) ; COPRO (40) ; ASL (40) ; AFUL (40)
- Numero_resolution_brut — Type SQLite : INTEGER. NULL observés : non (0/160). Valeurs distinctes non NULL : 2.
   Description : Numéro brut de la résolution
   Exemples : 1 ; 2
   Valeurs observées (effectif) : 2 (80) ; 1 (80)
- Numero_resolution_tri — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 2.
   Description : Numéro de tri (voir *Points d'attention*)
   Exemples : 001 ; 002
   Valeurs observées (effectif) : 002 (80) ; 001 (80)
- Indicateur_approbation_resolution — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 2.
   Description : Résolution approuvée
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Oui (80) ; Non (80)
- Description_resolution — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 2.
   Confidentialité : RGPD
   Description : Description
   Format / valeurs indicatives : Démission de la présidente, du secrétaire et du trésorier…
   Exemples : Travaux de renovation ; Approbation du budget
   Valeurs observées (effectif) : Travaux de renovation (80) ; Approbation du budget (80)
- Classification_resolution — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 2.
   Description : Classification
   Format / valeurs indicatives : BUDGET2015 … BUDGET2027 / TRAVAUX / HONORAIRE / CHANGEMENT / CONTRAT / PROCEDURE / PPPT / VIE / DEVIS / AUTRES
   Exemples : TRAVAUX ; BUDGET2026
   Valeurs observées (effectif) : TRAVAUX (80) ; BUDGET2026 (80)
- Montant_engage_resolution — Type SQLite : INTEGER. NULL observés : non (0/160). Valeurs distinctes non NULL : 2.
   Description : Montant engagé
   Exemples : 5000 ; 7500
   Valeurs observées (effectif) : 7500 (80) ; 5000 (80)
- Indicateur_dernier_document — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 1.
   Description : Dernier document connu
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (160)
- Lien_URL_GED — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 160.
   Confidentialité : RGPD
   Description : Lien GED
   Format / valeurs indicatives : https://…
   Exemples : https://ged.local/copro/AJ-COP-00001/1 ; https://ged.local/copro/AJ-COP-00001/2 ; https://ged.local/copro/AC-COP-00002/1
- Date_integration — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 160.
   Description : Intégration
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/160). Valeurs distinctes non NULL : 160.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Diagnostic
Nombre de lignes : 250
- ID_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Identifiant
   Format / valeurs indicatives : Code_societe-Numero_diagnostic (AC-018769)
   Exemples : AJ-018769 ; AC-018770 ; BSH-018771
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : AJ (63) ; AC (63) ; MF1 (62) ; BSH (62)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Code lot
   Format / valeurs indicatives : 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Numero_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Numéro du diagnostic
   Format / valeurs indicatives : 6 chiffres
   Exemples : 018769 ; 018770 ; 018771
   Format observé : 999999 (ex. 018769)
- Numero_dossier — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Numéro du dossier
   Format / valeurs indicatives : 6 chiffres
   Exemples : DOS-000001 ; DOS-000002 ; DOS-000003
   Format observé : AAA-999999 (ex. DOS-000001)
- Nature_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 5.
   Description : Nature
   Format / valeurs indicatives : AMI / CRP / DPE / EIE / EIG
   Exemples : AMI ; CRP ; DPE
   Valeurs observées (effectif) : EIG (50) ; EIE (50) ; DPE (50) ; CRP (50) ; AMI (50)
- Type_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 8.
   Description : Type
   Format / valeurs indicatives : DAP / DII / DIS / DTA / RAF / RAL / RAS / RAT
   Exemples : DAP ; DII ; DIS
   Valeurs observées (effectif) : DII (32) ; DAP (32) ; RAT (31) ; RAS (31) ; RAL (31) ; RAF (31) ; DTA (31) ; DIS (31)
- Code_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 14.
   Description : Nature-Type
   Format / valeurs indicatives : AMI-DAP / AMI-DTA / AMI-RAF / AMI-RAL / AMI-RAS / AMI-RAT / CRP-DII / CRP-DIS / DPE-DII / DPE-DIS / EIE-DII / EIE-DIS / EIG-DII / EIG-DIS
   Exemples : AMI-DAP ; AMI-DTA ; AMI-RAF
   Valeurs observées (effectif) : EIE-DIS (18) ; EIE-DII (18) ; DPE-DIS (18) ; DPE-DII (18) ; CRP-DIS (18) ; CRP-DII (18) ; AMI-RAT (18) ; AMI-RAS (18) ; AMI-RAL (18) ; AMI-RAF (18) ; AMI-DTA (18) ; AMI-DAP (18) ; EIG-DIS (17) ; EIG-DII (17)
- Libelle_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 5.
   Description : Libellé
   Format / valeurs indicatives : Diagnostic amiante partie privative / RAAT Façade / Localisé / Standard / Toiture / CREP / DPE et GES / EIIE / EIIG / Technique Amiante
   Exemples : DPE et GES ; Diagnostic amiante partie privative ; RAAT Façade
   Valeurs observées (effectif) : Standard (50) ; RAAT Façade (50) ; Localisé (50) ; Diagnostic amiante partie privative (50) ; DPE et GES (50)
- Date_injection_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Injection dans le système
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2023-12-27 ; 2023-12-28 ; 2023-12-29
   Format observé : AAAA-MM-JJ
- Date_debut_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Début de validité
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-01-01 ; 2024-01-02 ; 2024-01-03
   Format observé : AAAA-MM-JJ
- Date_fin_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Fin de validité
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2024-12-31 ; 2025-01-01 ; 2025-01-02
   Format observé : AAAA-MM-JJ
- Indicateur_diagnostic_le_plus_recent — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 2.
   Description : Diagnostic le plus récent
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (166) ; Oui (84)
- Indicateur_diagnostic_perime — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 1.
   Description : Diagnostic périmé
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (250)
- Nombre_jours_avant_peremption — Type SQLite : INTEGER. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Jours avant péremption
   Exemples : -646 ; -645 ; -644
   Plage observée : -646 à -397
- Lien_URL_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Confidentialité : RGPD
   Description : Lien du diagnostic
   Format / valeurs indicatives : https://…
   Exemples : https://ged.local/diagnostic/AJ-018769 ; https://ged.local/diagnostic/AC-018770 ; https://ged.local/diagnostic/BSH-018771
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
- Famille_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 10.
   Description : Famille du diagnostic (10 modalités, 25 lignes chacune). ATTENTION : indépendante de Nature_diagnostic, Code_diagnostic et Libelle_diagnostic dans cette base fictive (ex. Famille 'DPE' ⇒ Libelle 'RAAT Façade' ; Nature 'DPE' ⇒ Famille 'DPE' ou 'RAAT LO FACADE'). Pour identifier un DPE, ne pas se fier à un seul de ces champs ; pour la lettre DPE, passer par Diagnostic_valeur.Type_valeur = 'Lettre_DPE_EP'.
   Format / valeurs indicatives : CREP / DAPP / DPE / DTA / EIIE / EIIG / RAAT LO / RAAT LO FACADE / RAAT LO TOITURE / RAAT ST
   Exemples : CREP ; DAPP ; DPE
   Valeurs observées (effectif) : RAAT ST (25) ; RAAT LO TOITURE (25) ; RAAT LO FACADE (25) ; RAAT LO (25) ; EIIG (25) ; EIIE (25) ; DTA (25) ; DPE (25) ; DAPP (25) ; CREP (25)
- Lien_IKOS_GED_diagnostic — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Confidentialité : RGPD
   Description : Lien IKOS GED
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/ged/AJ-018769 ; https://ikos.local/ged/AC-018770 ; https://ikos.local/ged/BSH-018771

## Diagnostic_valeur
Nombre de lignes : 500
- ID_diagnostic — Type SQLite : TEXT. NULL observés : non (0/500). Valeurs distinctes non NULL : 250.
   Description : Diagnostic
   Format / valeurs indicatives : AC-018769
   Exemples : AJ-018769 ; AC-018770 ; BSH-018771
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/500). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : AJ (126) ; AC (126) ; MF1 (124) ; BSH (124)
- Numero_diagnostic — Type SQLite : TEXT. NULL observés : non (0/500). Valeurs distinctes non NULL : 250.
   Description : Numéro du diagnostic
   Format / valeurs indicatives : 6 chiffres
   Exemples : 018769 ; 018770 ; 018771
   Format observé : 999999 (ex. 018769)
- Type_valeur — Type SQLite : TEXT. NULL observés : non (0/500). Valeurs distinctes non NULL : 5.
   Description : Nature de la valeur. 5 modalités exactes (sensibles à la casse) : Lettre_DPE_EP ; Valeur_CREP ; Valeur_DAPP ; Valeur_DTA_liste_A_1 ; Valeur_EIIE. 100 lignes chacune, 2 Type_valeur par diagnostic.
   Remarque : ATTENTION : dans cette base fictive, Type_valeur n'est PAS cohérent avec Diagnostic.Famille_diagnostic (voir « Anomalies connues » n°1). Ne pas combiner un filtre de famille (ex. 'DPE') avec Type_valeur = 'Lettre_DPE_EP' : le résultat est vide.
   Format / valeurs indicatives : Valeur_DTA_liste_A_1 / Lettre_DPE_EP / Valeur_EIIE / Valeur_CREP / Valeur_DAPP…
   Exemples : Valeur_DTA_liste_A_1 ; Lettre_DPE_EP ; Valeur_EIIE
   Valeurs observées (effectif) : Valeur_EIIE (100) ; Valeur_DTA_liste_A_1 (100) ; Valeur_DAPP (100) ; Valeur_CREP (100) ; Lettre_DPE_EP (100)
- Valeur — Type SQLite : REAL (affinité) ; valeurs MIXTES : REAL pour les Type_valeur « Valeur_* », TEXT (lettre A à G) pour « Lettre_DPE_EP ». NULL observés : non (0/500). Valeurs distinctes non NULL : 407.
   Description : Valeur du diagnostic. Son type dépend de Type_valeur : lettre d'étiquette énergie A / B / C / D / E / F / G (TEXT) quand Type_valeur = 'Lettre_DPE_EP' ; nombre (REAL) pour tous les autres Type_valeur.
   Remarque : Toujours filtrer d'abord sur Type_valeur avant de comparer Valeur (ne jamais appliquer une comparaison numérique aux lettres, ni IN ('F','G') aux nombres). Seuils de correspondance DPE énergie primaire (kWh/m²/an) utilisés pour générer les lettres : A ≤ 70 ; B ≤ 110 ; C ≤ 180 ; D ≤ 250 ; E ≤ 330 ; F ≤ 420 ; G > 420.
   Exemples : 10.0 ; 11.5 ; 13.0
   Plage observée : nombres de 10.0 à 758.5 (Valeur_*) ; lettres (Lettre_DPE_EP) : A (8) ; B (6) ; C (9) ; D (9) ; E (11) ; F (12) ; G (45)
- Unite — Type SQLite : TEXT. NULL observés : non (0/500). Valeurs distinctes non NULL : 14.
   Description : Unité. 14 modalités observées, réparties de façon uniforme et sans lien avec Type_valeur (ex. une lettre DPE porte une unité 'M2' ou 'CAL'). Unité non fiable : ne pas l'utiliser pour filtrer ou interpréter une valeur.
   Format / valeurs indicatives : U / KWH / NULL
   Exemples : M3 ; LG ; M
   Valeurs observées (effectif) : U (36) ; ST (36) ; RLX (36) ; ML (36) ; M2 (36) ; M (36) ; LG (36) ; H (36) ; FFT (36) ; F (36) ; CAL (36) ; M3 (35) ; % (35) ; E (34)

## Equipement
Nombre de lignes : 400
- ID_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Identifiant
   Format / valeurs indicatives : Code_type_equipement-Code_niveau_patrimoine (CHIN-0008-KRA)
   Exemples : AJ-000001-EQ-0001 ; AC-000002-EQ-0002 ; BSH-000003-EQ-0003
- ID_patrimoine_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Lot ou patrimoine d'implantation
   Format / valeurs indicatives : Format ID_lot ou ID_patrimoine
   Exemples : AJ-AJ01-01-01-AJ-000001 ; AC-AC02-02-02-AC-000002 ; BSH-BS03-03-03-BSH-000003
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (100) ; BSH (100) ; AJ (100) ; AC (100)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 80.
   Description : Patrimoine niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 9.
   Description : Patrimoine niveau 2
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (45) ; 07 (45) ; 06 (45) ; 05 (45) ; 04 (45) ; 03 (45) ; 02 (45) ; 01 (45) ; 09 (40)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 12.
   Description : Patrimoine niveau 3
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (35) ; 07 (35) ; 06 (35) ; 05 (35) ; 04 (35) ; 03 (35) ; 02 (35) ; 01 (35) ; 12 (30) ; 11 (30) ; 10 (30) ; 09 (30)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Lot
   Format / valeurs indicatives : 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Niveau_patrimoine_lot_rattachement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Niveau de rattachement
   Format / valeurs indicatives : Bâtiment / Lot / Cage d'escalier / Résidence / Stationnement
   Exemples : Lot
   Valeurs observées (effectif) : Lot (400)
- Code_famille_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Famille (code)
   Format / valeurs indicatives : VEN / PLO / PCO / FAC / AMX / SEC / MEX / ELE / COV / CHA
   Exemples : VEN ; PLO ; PCO
   Valeurs observées (effectif) : VEN (40) ; SEC (40) ; PLO (40) ; PCO (40) ; MEX (40) ; FAC (40) ; ELE (40) ; COV (40) ; CHA (40) ; AMX (40)
- Libelle_famille_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Famille (libellé)
   Format / valeurs indicatives : Plomberie - sanitaire / Aménagements extérieurs et stationnement / Electricité / Sécurité et sûreté / Menuiseries extérieures / Parties communes / Ventilation / Couvert / Chauffage et ECS / Façade
   Exemples : Ventilation ; Plomberie - sanitaire ; Parties communes
   Valeurs observées (effectif) : Ventilation (40) ; Sécurité et sûreté (40) ; Plomberie - sanitaire (40) ; Parties communes (40) ; Menuiseries extérieures (40) ; Façade (40) ; Electricité (40) ; Couvert (40) ; Chauffage et ECS (40) ; Aménagements extérieurs et stationnement (40)
- Code_type_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Type (code)
   Format / valeurs indicatives : RELE / FACA / COUV / FENE / CHIN / GACO / GACT / SOPC / ECSI / DESE / LVIE / OCCU / SANL / REAS / VOIR / PASO / VMCI / PELO / CHCO / TGAZ / VMCC / SURP / TOTE / IELO / BALC / INTE / IEPC / PLPC / ASCE / MUPC / PBOX / PAUT / CHAS / PLOL / REEP
   Exemples : VMC ; CHA ; POR
   Valeurs observées (effectif) : VMC (100) ; POR (100) ; ELE (100) ; CHA (100)
- Libelle_type_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Type (libellé)
   Format / valeurs indicatives : Installation électrique Logements / Interphonie / Contrôle d'accès / VMC individuelle / Fenêtre/porte-fenêtre / Châssis de toit / Panneaux solaires / Installations de plomberie logements / Couverture / Revêtements de plafond / Toiture terrasse / Trappe de désenfumage cage esc. / Porte de box / Murs de façade / Occultations / Installations sanitaires logements / Voirie / Surpresseur / Lignes de vie / ECS individuelle / Chauffage individuel / Revêtements muraux / Revêtements de sol / Pompe de relevage / Tige cuisine gaz / Porte palière logements / Chauffage collectif / Réseaux d'eau potable / Garde-corps / VMC collective / Porte automatique / Installation électrique Parties communes / Réseaux d'assainissement / Ascenseur / Balcon / Garde-corps (protection collective)
   Exemples : VMC ; Chaudiere ; Porte
   Valeurs observées (effectif) : VMC (100) ; Tableau electrique (100) ; Porte (100) ; Chaudiere (100)
- Code_nature_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Nature (code)
   Format / valeurs indicatives : AUTOR / INERT / CCOGA / GGSTA / CHBAI / VAUTR / GVMCG / SECTI / ITEX / CONVE / LEVAN / INTDI / GACOP / EXSTA / NULL / INTBO / VISIO / ITIN / PACHA / BALLO / PASOP / CCFUE / COULI / HYGRA / DBFLX / RAYON / CCBOI / HYGRB / VNATU / VMCGZ / CCACC / BASCU / BATTA / VROUL / GACOL / GGVEN / GG3CE / BATHR / BASOL / CCUCI / INTDE
   Exemples : IND ; COL
   Valeurs observées (effectif) : IND (200) ; COL (200)
- Libelle_nature_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Nature (libellé)
   Format / valeurs indicatives : Ballon solaire / Convecteur (élec.) / Générateur gaz sur stato mécanique/naturelle / ITI / Chaufferie au gaz naturel / Chauffage urbain de type CIC / Extracteur stato-mécanique / Inertie (élec.) / Chaufferie bois / Chaufferie fuel / Battante / Garde-corps extérieurs logements / Rayonnant/radiant (élec.) / Générateur sur VMC gaz / Visiophone / ITE / Pompe à chaleur (élec.) / Levante / Basculante / Hygro A / Hygro B / Contrôle d'accès / Coulissante / Ventilation naturelle / Interphone à défilement / Interphone à bouton / Interphone à digicode / Autre type / Garde-corps extérieurs parties communes / Générateur gaz sur conduit 3CEP / Générateur gaz sur ventouse / VMC gaz / Ballon thermodynamique / Chauffe-bain gaz / Double flux / Photovoltaïque / Autoréglable / Volet roulant intégré / Sectionnable / Ballon électrique / NULL
   Exemples : Individuel ; Collectif
   Valeurs observées (effectif) : Individuel (200) ; Collectif (200)
- Code_materiaux_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Description : Matériau (code)
   Format / valeurs indicatives : BOISS / PVINY / NULL / FBARD / FENDU / ALUMI
   Exemples : BOISS ; PVINY ; FBARD
   Valeurs observées (effectif) : PVINY (80) ; FENDU (80) ; FBARD (80) ; BOISS (80) ; ALUMI (80)
- Libelle_materiaux_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Description : Matériau (libellé)
   Format / valeurs indicatives : Bois / PVC / Aluminium / Finition enduit / Finition bardage / NULL
   Exemples : Bois ; PVC ; Aluminium
   Valeurs observées (effectif) : PVC (80) ; Finition enduit (80) ; Finition bardage (80) ; Bois (80) ; Aluminium (80)
- Libelle_emplacement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Emplacement
   Format / valeurs indicatives : NULL
   Exemples : Cuisine ; Toiture ; Cave
   Valeurs observées (effectif) : Toiture (100) ; Hall (100) ; Cuisine (100) ; Cave (100)
- Indicateur_pseudo_equipement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Pseudo-équipement
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- ID_equipement_rattachement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Équipement parent
   Format / valeurs indicatives : NULL
   Exemples : AJ-000001-EQ-0001 ; AC-000002-EQ-0001 ; BSH-000003-EQ-0002
- Unite_principale — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Unité de quantité principale
   Format / valeurs indicatives : M² / NB / MI / NULL
   Exemples : NB
   Valeurs observées (effectif) : NB (400)
- Quantite_nombre — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Quantité (nombre)
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 4 (100) ; 3 (100) ; 2 (100) ; 1 (100)
- Quantite_surface — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 30.
   Description : Quantité (surface)
   Exemples : 10 ; 11 ; 12
   Plage observée : 10 à 39
- Quantite_lineaire — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Quantité (linéaire)
   Exemples : 2 ; 3 ; 4
   Valeurs observées (effectif) : 11 (40) ; 10 (40) ; 9 (40) ; 8 (40) ; 7 (40) ; 6 (40) ; 5 (40) ; 4 (40) ; 3 (40) ; 2 (40)
- Indicateur_activite — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Équipement actif
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Date_installation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Installation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2015-01-01 ; 2016-01-01 ; 2017-01-01
   Valeurs observées (effectif) : 2024-01-01 (40) ; 2023-01-01 (40) ; 2022-01-01 (40) ; 2021-01-01 (40) ; 2020-01-01 (40) ; 2019-01-01 (40) ; 2018-01-01 (40) ; 2017-01-01 (40) ; 2016-01-01 (40) ; 2015-01-01 (40)
- Date_mise_en_service — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Mise en service
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2015-02-01 ; 2016-02-01 ; 2017-02-01
   Valeurs observées (effectif) : 2024-02-01 (40) ; 2023-02-01 (40) ; 2022-02-01 (40) ; 2021-02-01 (40) ; 2020-02-01 (40) ; 2019-02-01 (40) ; 2018-02-01 (40) ; 2017-02-01 (40) ; 2016-02-01 (40) ; 2015-02-01 (40)
- Date_fin_de_service — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Fin de service
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2030-12-31
   Valeurs observées (effectif) : 2030-12-31 (400)
- Marque — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Marque
   Format / valeurs indicatives : NULL
   Exemples : Atlantic ; Legrand ; Schneider
   Valeurs observées (effectif) : Schneider (100) ; Legrand (100) ; Daikin (100) ; Atlantic (100)
- Modele — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 100.
   Description : Modèle
   Format / valeurs indicatives : NULL
   Exemples : MOD-000 ; MOD-001 ; MOD-002
- Puissance — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 20.
   Description : Puissance
   Format / valeurs indicatives : NULL
   Exemples : 2 kW ; 3 kW ; 4 kW
- Capacite — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Capacité
   Format / valeurs indicatives : NULL
   Exemples : 100 L ; 101 L ; 102 L
- Mode_fonctionnement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Mode de fonctionnement
   Format / valeurs indicatives : NULL
   Exemples : Automatique
   Valeurs observées (effectif) : Automatique (400)
- Numero_serie_constructeur — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : N° de série constructeur
   Format / valeurs indicatives : NULL
   Exemples : SN00000001 ; SN00000002 ; SN00000003
   Format observé : AA99999999 (ex. SN00000001)
- Indicateur_iot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Équipement connecté
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (300) ; Oui (100)
- Numero_serie_boitier_iot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 101.
   Description : N° de série du boîtier IoT
   Exemples : IOT00000001 ; N/A ; IOT00000005
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Geographie
Nombre de lignes : 100
- Code_INSEE_commune — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 100.
   Description : Code INSEE
   Format / valeurs indicatives : 5 chiffres
   Exemples : 35000 ; 35001 ; 35002
   Format observé : 99999 (ex. 35000)
- Libelle_commune — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 6.
   Description : Commune
   Format / valeurs indicatives : Sannois, Santeuil, Sarcelles
   Exemples : RENNES ; NANTES ; BREST
   Valeurs observées (effectif) : RENNES (17) ; NANTES (17) ; LORIENT (17) ; BREST (17) ; VANNES (16) ; SAINT-MALO (16)
- Code_departement — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 5.
   Description : Département (code)
   Format / valeurs indicatives : 2 ou 3 chiffres
   Exemples : 35 ; 36 ; 37
   Valeurs observées (effectif) : 39 (20) ; 38 (20) ; 37 (20) ; 36 (20) ; 35 (20)
- Libelle_departement — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 5.
   Description : Département
   Format / valeurs indicatives : Guadeloupe, Eure
   Exemples : ILLE-ET-VILAINE ; LOIRE-ATLANTIQUE ; FINISTERE
   Valeurs observées (effectif) : MORBIHAN (20) ; LOIRE-ATLANTIQUE (20) ; ILLE-ET-VILAINE (20) ; FINISTERE (20) ; COTES-D'ARMOR (20)
- Code_region — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 1.
   Description : Région (code)
   Format / valeurs indicatives : 2 chiffres
   Exemples : 53
   Valeurs observées (effectif) : 53 (100)
- Code_EPCI — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 20.
   Description : EPCI (code)
   Format / valeurs indicatives : 9 chiffres
   Exemples : EPCI001 ; EPCI002 ; EPCI003
   Format observé : AAAA999 (ex. EPCI001)
- Nature_EPCI — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 3.
   Description : Nature de l'EPCI
   Format / valeurs indicatives : ME / ZZ / CA / CU / CC / METLYON
   Exemples : CA ; CC ; CU
   Valeurs observées (effectif) : CA (34) ; CU (33) ; CC (33)
- Libelle_EPCI — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 3.
   Description : EPCI
   Format / valeurs indicatives : CC Berg et Coiron / CA Arche Agglo
   Exemples : Rennes Metropole ; Nantes Metropole ; Golfe du Morbihan
   Valeurs observées (effectif) : Rennes Metropole (34) ; Nantes Metropole (33) ; Golfe du Morbihan (33)
- Zonage_1_2_3 — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 3.
   Description : Zonage 1-2-3
   Format / valeurs indicatives : 01 / 02 / 03
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 01 (34) ; 03 (33) ; 02 (33)
- Zonage_ABC — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 4.
   Description : Zonage ABC
   Format / valeurs indicatives : A / B1 / B2 / C
   Exemples : A ; B1 ; B2
   Valeurs observées (effectif) : C (25) ; B2 (25) ; B1 (25) ; A (25)
- Zonage_TLV — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 3.
   Description : Zonage taxe sur les logements vacants
   Format / valeurs indicatives : Zone tendue / Non tendue / Zone touristique et tendue / NULL
   Exemples : Zone tendue ; Non tendue ; Zone touristique et tendue
   Valeurs observées (effectif) : Zone tendue (34) ; Zone touristique et tendue (33) ; Non tendue (33)
- Zonage_ZRR_FRR — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 2.
   Description : Zonage de revitalisation rurale
   Format / valeurs indicatives : FRR / ZRR / NULL
   Exemples : FRR ; ZRR
   Valeurs observées (effectif) : ZRR (50) ; FRR (50)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/100). Valeurs distinctes non NULL : 100.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Intervention
Nombre de lignes : 400
- ID_intervention — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Identifiant
   Format / valeurs indicatives : Code_societe-Numero_intervention
   Exemples : AJ-011065-INT-0001 ; AC-011066-INT-0002 ; BSH-011067-INT-0003
- ID_commande — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 300.
   Description : Commande
   Format / valeurs indicatives : AC-011065
   Exemples : AJ-011065 ; AC-011066 ; BSH-011067
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Lot
   Format / valeurs indicatives : AC-376745
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- Numero_intervention — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Numéro de l'intervention
   Exemples : 1 ; 2 ; 3
   Plage observée : 1 à 400
- Code_lot_intervention — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Code lot de l'intervention
   Format / valeurs indicatives : 2 ou 3 lettres et chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Code_intervention — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Code de l'intervention
   Format / valeurs indicatives : Lettres majuscules et chiffres
   Exemples : ASC ; VMC ; PLB
   Valeurs observées (effectif) : VMC (100) ; PLB (100) ; ELE (100) ; ASC (100)
- Libelle_intervention — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Libellé
   Format / valeurs indicatives : WC 2 couches, Plomberie
   Exemples : Ascenseur ; Ventilatio ; Plomberie
   Valeurs observées (effectif) : Ventilatio (100) ; Plomberie (100) ; Electricit (100) ; Ascenseur (100)
- Date_realisation_intervention — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Réalisation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-01 ; 2025-01-02 ; 2025-01-03
   Format observé : AAAA-MM-JJ
- Date_enregistrement_commande — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 300.
   Description : Enregistrement de la commande
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-01 ; 2025-01-02 ; 2025-01-03
   Format observé : AAAA-MM-JJ
- Quantite — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Description : Quantité
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 5 (80) ; 4 (80) ; 3 (80) ; 2 (80) ; 1 (80)
- Unite — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : Unité
   Format / valeurs indicatives : M3 / LG / M / FFT / H / ST / M2 / F / CAL / U / RLX / ML / % / E
   Exemples : U ; H ; M2
   Valeurs observées (effectif) : U (134) ; M2 (133) ; H (133)
- Prix_unitaire_HT — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 100.
   Description : Prix unitaire HT
   Exemples : 50 ; 51 ; 52
   Plage observée : 50 à 149
- Montant_total_HT — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 95.
   Description : Montant HT
   Exemples : 50 ; 102 ; 156
   Plage observée : 50 à 745
- Prix_unitaire_TVA — Type SQLite : REAL. NULL observés : non (0/400). Valeurs distinctes non NULL : 100.
   Description : Prix unitaire de TVA
   Exemples : 10.0 ; 10.2 ; 10.4
   Plage observée : 10.0 à 29.8
- Montant_total_TTC — Type SQLite : REAL. NULL observés : non (0/400). Valeurs distinctes non NULL : 95.
   Description : Montant TTC
   Exemples : 60.0 ; 122.4 ; 187.2
   Plage observée : 60.0 à 894.0
- Code_schema_comptable — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 20.
   Description : Schéma comptable
   Format / valeurs indicatives : 2 ou 3 lettres et chiffres
   Exemples : SC00 ; SC01 ; SC02
   Format observé : AA99 (ex. SC00)
- Livrable_attendu — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 6.
   Description : Livrable attendu
   Format / valeurs indicatives : EIIE / DTA / DAPP / DPE / EIIG / RAAT ST
   Exemples : EIIE ; DTA ; DAPP
   Valeurs observées (effectif) : EIIE (67) ; DTA (67) ; DPE (67) ; DAPP (67) ; RAAT ST (66) ; EIIG (66)
- Date_realisation_livrable — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Réalisation du livrable
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-02-01 ; 2025-02-02 ; 2025-02-03
   Format observé : AAAA-MM-JJ
- Indicateur_livrable_valide — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Livrable validé
   Format / valeurs indicatives : Oui / Non
   Exemples : Non ; Oui
   Valeurs observées (effectif) : Oui (300) ; Non (100)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Lot
Nombre de lignes : 400
- ID_client_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Identifiant client/lot
   Format / valeurs indicatives : CLT-AC-026905-LOT-AC-014311
   Exemples : CLT-AJ-003301-LOT-AJ-000001 ; CLT-AC-003302-LOT-AC-000002 ; CLT-BSH-003303-LOT-BSH-000003
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Identifiant du lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 80.
   Description : Patrimoine
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- ID_RPLS — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Identifiant RPLS
   Format / valeurs indicatives : 10 chiffres (0027809625)
   Exemples : RPLS-AJ-000001 ; RPLS-AC-000002 ; RPLS-BSH-000003
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (100) ; BSH (100) ; AJ (100) ; AC (100)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Code lot
   Format / valeurs indicatives : 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 80.
   Description : Patrimoine niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 9.
   Description : Patrimoine niveau 2
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (45) ; 07 (45) ; 06 (45) ; 05 (45) ; 04 (45) ; 03 (45) ; 02 (45) ; 01 (45) ; 09 (40)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 12.
   Description : Patrimoine niveau 3
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (35) ; 07 (35) ; 06 (35) ; 05 (35) ; 04 (35) ; 03 (35) ; 02 (35) ; 01 (35) ; 12 (30) ; 11 (30) ; 10 (30) ; 09 (30)
- Libelle_activite_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Activité
   Format / valeurs indicatives : Locatif / Accession / Autres
   Exemples : Locatif
   Valeurs observées (effectif) : Locatif (400)
- Libelle_usage_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Usage
   Format / valeurs indicatives : Commerce / Autre / Terrain / Dépendance / Foyer / Panneau publicitaire / Espace commun / Logement / Stationnement
   Exemples : Logement
   Valeurs observées (effectif) : Logement (400)
- Code_nature_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Nature (code)
   Format / valeurs indicatives : DEP / EQU / STN / TER / ZFI / PPB / PK / SLA / GEN / LVM / ESC / LGU / FOA / FOU / LAA / LGA / STA / FOY / DPA / STU / EXT / CCV / PC / LGT / LLA / SVM
   Exemples : LOG
   Valeurs observées (effectif) : LOG (400)
- Libelle_nature_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Nature (libellé)
   Format / valeurs indicatives : Logement Vente Mandat / local activité accession / Fact. interne (Fictive) / espace commun / logement / stationnement / Parkings / Gendarmerie / Clos couvert / Hall & parties communes / local activité / Foyer / logement locatif / Stationn. Vente Mandat / Parties communes / Logt location accession / stationnement accession / Dépendance Accession / stationnement locatif / logement Accession / Terrain / logement Usuf. Loc. Soc / Equipements divers / dépendance / Foyer Accession (Copro) / Espaces extérieurs / Stn Location accession / station. Usuf. Loc. Soc. / Foyer Usuf.Loc.Soc. / panneau publicitaire / NULL
   Exemples : Logement
   Valeurs observées (effectif) : Logement (400)
- Code_partie_commune_privative — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Partie privative ou commune (code)
   Format / valeurs indicatives : P / C
   Exemples : P
   Valeurs observées (effectif) : P (400)
- Libelle_partie_commune_privative — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Libellé
   Format / valeurs indicatives : Partie commune / Partie privative
   Exemples : Partie privative
   Valeurs observées (effectif) : Partie privative (400)
- Etage — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 6.
   Description : Étage
   Format / valeurs indicatives : -2 à 19
   Exemples : 0 ; 1 ; 2
   Valeurs observées (effectif) : 3 (67) ; 2 (67) ; 1 (67) ; 0 (67) ; 5 (66) ; 4 (66)
- Numero_porte — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 5.
   Confidentialité : RGPD
   Description : Numéro de porte
   Format / valeurs indicatives : PP24 / G56 / 9117 / 2C / L17
   Exemples : PP24 ; G56 ; 9117
   Valeurs observées (effectif) : PP24 (80) ; L17 (80) ; G56 (80) ; 9117 (80) ; 2C (80)
- Rang_numero_porte_par_etage — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Rang de la porte dans l'étage
   Format / valeurs indicatives : 1 à 3 chiffres
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 10 (40) ; 9 (40) ; 8 (40) ; 7 (40) ; 6 (40) ; 5 (40) ; 4 (40) ; 3 (40) ; 2 (40) ; 1 (40)
- Code_individuel_collectif — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Individuel/collectif (code)
   Format / valeurs indicatives : MIX / COL / IND
   Exemples : IND
   Valeurs observées (effectif) : IND (400)
- Libelle_individuel_collectif — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Libellé
   Format / valeurs indicatives : (Individuel/collectif) / Individuel / Collectif
   Exemples : Individuel
   Valeurs observées (effectif) : Individuel (400)
- Code_categorie_financement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : Financement (code)
   Format / valeurs indicatives : PUS / PAL / PTS / ASP / PLI / PSL / HLM / PLS / PLA / AIM / PAP / FPR / HMA / ILM / PLM / PLR / PSR / DIV / RSF / PLU
   Exemples : PLUS ; PLAI ; PLS
   Valeurs observées (effectif) : PLUS (134) ; PLS (133) ; PLAI (133)
- Libelle_categorie_financement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : Financement (libellé)
   Format / valeurs indicatives : Prog loyer intermédiaire / Prêt locatif d'urgence / Prêt loc. aidé très soc. / Réhabilitation PALULOS / Prog loyer réduit / Accession sans prêt / Réhabil sans financement / Location accession / Prêt loc à usage social / Immeuble à loyer moyen / Prêt locatif social / Accession immobilisée / Divers / Habitat à loyer modéré / Prêt accession propriété / HLM Accession / PSR / Fonds propres / Prêt locatif loyer modér / Prêt locatif aidé / NULL
   Exemples : PLUS ; PLAI ; PLS
   Valeurs observées (effectif) : PLUS (134) ; PLS (133) ; PLAI (133)
- Code_type_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Type de lot (code)
   Format / valeurs indicatives : BRS / GAR / ANT / T1 / JAR / BUR / FJT / PSS / PAE / BUA / PRK / T3 / FPA / T6 / LCR / T2 / T4 / 3*4 / BOX / T7 / T1B / CAV / CHA / CEL / FAH / BSS / CMC / BAE / T5 / DIV
   Exemples : APP
   Valeurs observées (effectif) : APP (400)
- Libelle_type_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Type de lot (libellé)
   Format / valeurs indicatives : Foyer adultes handicapés / Cave / Type 1 à 7 / Type 1 Bis / Foyer jeune travailleur / Parking aérien / Parking couvert / Parking sous-terrain / Bureau Bat. admn. loué / Bureau / Box aérien / Box sous-terrain / Box / Bail Réel Solidaire / Foyer personnes âgées / Antenne / Commerce / Divers / Local commun résidentiel / Panneau publ. 3m X 4m / Jardins familiaux / Chambre / Garage / Cellier / NULL
   Exemples : Appartement
   Valeurs observées (effectif) : Appartement (400)
- Code_niveau_adaptation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Niveau d'adaptation (code)
   Format / valeurs indicatives : AH0–AH3 / A0–A3 / A+0–A+3 / HN1 / HN2 / NA0–NA3 / PA2
   Exemples : NA0 ; AH1 ; A2
   Valeurs observées (effectif) : PA2 (100) ; NA0 (100) ; AH1 (100) ; A2 (100)
- Libelle_niveau_adaptation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Niveau d'adaptation (libellé)
   Format / valeurs indicatives : Adapté + H/PA / Adapté PA / Non adapté, adaptable PA / Adapté + PA / Adapté + H / Adaptable H/PA / Non adapté, peu adaptable PA / Adapté H/PA / NULL
   Exemples : Adapté PA ; Adaptable H/PA ; Adapté + PA
   Valeurs observées (effectif) : Adapté PA (100) ; Adapté + PA (100) ; Adapté + H (100) ; Adaptable H/PA (100)
- Indicateur_niveau_adaptation_partie_commune — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Adaptation des parties communes
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Oui (200) ; Non (200)
- Indicateur_niveau_adaptation_partie_privative_public_cible — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Adaptation privative (public cible)
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Indicateur_niveau_adaptation_partie_privative_service — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Adaptation privative (service)
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Code_niveau_adaptation_classification_USH — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Classification USH
   Format / valeurs indicatives : Niveau 1 / Niveau 2 / Niveau 3 / Niveau 4
   Exemples : Niveau 1 ; Niveau 2 ; Niveau 3
   Valeurs observées (effectif) : Niveau 4 (100) ; Niveau 3 (100) ; Niveau 2 (100) ; Niveau 1 (100)
- Code_niveau_adaptation_classification_ARO — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Classification ARO
   Format / valeurs indicatives : PA1 / PA2 / PA1-NC / PA2-NC / H1 / H2 / H3
   Exemples : PA1 ; PA2 ; H1
   Valeurs observées (effectif) : PA2 (100) ; PA1 (100) ; H2 (100) ; H1 (100)
- Code_niveau_adaptation_classification_RPLS — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : Classification RPLS
   Format / valeurs indicatives : 11 / 12 / 13
   Exemples : 11 ; 12 ; 13
   Valeurs observées (effectif) : 11 (134) ; 13 (133) ; 12 (133)
- Code_niveau_adaptation_classification_Rennes_Metropole — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : Classification Rennes Métropole
   Format / valeurs indicatives : LAP 0 / LAP1 / LAP2
   Exemples : LAP 0 ; LAP1 ; LAP2
   Valeurs observées (effectif) : LAP 0 (134) ; LAP2 (133) ; LAP1 (133)
- Surface_habitable — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 90.
   Description : Surface habitable
   Exemples : 35 ; 36 ; 37
   Plage observée : 35 à 124
- Nombre_chambres — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Nombre de chambres
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 4 (100) ; 3 (100) ; 2 (100) ; 1 (100)
- Date_construction — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 80.
   Description : Construction
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 1970-01-01 ; 1971-02-04 ; 1972-03-07
   Format observé : AAAA-MM-JJ
- Date_reception_travaux — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Réception des travaux
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-06-15 ; 2011-06-15 ; 2012-06-15
   Valeurs observées (effectif) : 2019-06-15 (40) ; 2018-06-15 (40) ; 2017-06-15 (40) ; 2016-06-15 (40) ; 2015-06-15 (40) ; 2014-06-15 (40) ; 2013-06-15 (40) ; 2012-06-15 (40) ; 2011-06-15 (40) ; 2010-06-15 (40)
- Date_livraison — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Livraison
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-09-01 ; 2011-09-01 ; 2012-09-01
   Valeurs observées (effectif) : 2019-09-01 (40) ; 2018-09-01 (40) ; 2017-09-01 (40) ; 2016-09-01 (40) ; 2015-09-01 (40) ; 2014-09-01 (40) ; 2013-09-01 (40) ; 2012-09-01 (40) ; 2011-09-01 (40) ; 2010-09-01 (40)
- Date_mise_en_service — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Mise en service
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-10-01 ; 2011-10-01 ; 2012-10-01
   Valeurs observées (effectif) : 2019-10-01 (40) ; 2018-10-01 (40) ; 2017-10-01 (40) ; 2016-10-01 (40) ; 2015-10-01 (40) ; 2014-10-01 (40) ; 2013-10-01 (40) ; 2012-10-01 (40) ; 2011-10-01 (40) ; 2010-10-01 (40)
- Nombre_jours_depuis_mise_en_service — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Jours depuis la mise en service
   Exemples : 5851 ; 5486 ; 5120
   Valeurs observées (effectif) : 5851 (40) ; 5486 (40) ; 5120 (40) ; 4755 (40) ; 4390 (40) ; 4025 (40) ; 3659 (40) ; 3294 (40) ; 2929 (40) ; 2564 (40)
- Date_debut_commercialisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 10.
   Description : Début de commercialisation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-10-15 ; 2011-10-15 ; 2012-10-15
   Valeurs observées (effectif) : 2019-10-15 (40) ; 2018-10-15 (40) ; 2017-10-15 (40) ; 2016-10-15 (40) ; 2015-10-15 (40) ; 2014-10-15 (40) ; 2013-10-15 (40) ; 2012-10-15 (40) ; 2011-10-15 (40) ; 2010-10-15 (40)
- Indicateur_debut_commercialisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Commercialisation débutée
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Nombre_baux_lot — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Nombre de baux
   Exemples : 1
   Valeurs observées (effectif) : 1 (400)
- Indicateur_premiere_mise_en_location — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Première mise en location
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Indicateur_fin_gestion — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Fin de gestion
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Code_etat_actuel — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : État actuel (code)
   Format / valeurs indicatives : ATD / VVT / VCO / LO / VP / MES / FBE / ACO / VDO / VTE / HS / VCT / VDB / VRE / AVA / RRE / TRX / VDE / DML / NLO / MEL
   Exemples : OCC
   Valeurs observées (effectif) : OCC (400)
- Libelle_etat_actuel — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : État actuel (libellé)
   Format / valeurs indicatives : Vacance pour travaux / vendu à autre bailleur / Projet réhabilitation / Vendu / Mise en service / Vacances territoires / Att. valid. affectation / Vacance réservée / démolition / Mise en location (neuf) / Vacance ordinaire / Vacance partielle / Location ordinaire / Arret commercialisation / Attente démolition / Vacance détachement STN / Hors service / vendu à l'occupant / Attente de vente / Fin bail emphytéotique / UG non louée (Agc/siège) / NULL
   Exemples : Occupe
   Valeurs observées (effectif) : Occupe (400)
- Indicateur_exploitation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : En exploitation
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Indicateur_disponibilite_commercialisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Description : Disponible à la commercialisation
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Lien_IKOS_synthese_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Lien IKOS
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/lot/AJ-000001 ; https://ikos.local/lot/AC-000002 ; https://ikos.local/lot/BSH-000003
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Lot_historique
Nombre de lignes : 900
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 400.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- ID_lot_annee_mois — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 900.
   Description : Lot et mois
   Format / valeurs indicatives : AC-001892-2024-03
   Exemples : AJ-000001-2025-01 ; AC-000002-2025-02 ; BSH-000003-2025-03
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 80.
   Description : Patrimoine
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- Annee_mois — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 12.
   Description : Mois
   Format / valeurs indicatives : AAAA-MM
   Exemples : 2025-01-01 ; 2025-02-01 ; 2025-03-01
   Valeurs observées (effectif) : 2025-12-01 (75) ; 2025-11-01 (75) ; 2025-10-01 (75) ; 2025-09-01 (75) ; 2025-08-01 (75) ; 2025-07-01 (75) ; 2025-06-01 (75) ; 2025-05-01 (75) ; 2025-04-01 (75) ; 2025-03-01 (75) ; 2025-02-01 (75) ; 2025-01-01 (75)
- Annee_mois_ordre — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 12.
   Description : Mois, format de tri
   Format / valeurs indicatives : AAAAMM (202401)
   Exemples : 13 ; 14 ; 15
   Valeurs observées (effectif) : 24 (75) ; 23 (75) ; 22 (75) ; 21 (75) ; 20 (75) ; 19 (75) ; 18 (75) ; 17 (75) ; 16 (75) ; 15 (75) ; 14 (75) ; 13 (75)
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (225) ; BSH (225) ; AJ (225) ; AC (225)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 400.
   Description : Code lot
   Format / valeurs indicatives : 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 80.
   Description : Patrimoine niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 9.
   Description : Patrimoine niveau 2
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 02 (102) ; 01 (102) ; 08 (101) ; 07 (101) ; 06 (101) ; 05 (101) ; 04 (101) ; 03 (101) ; 09 (90)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 12.
   Description : Patrimoine niveau 3
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (79) ; 07 (79) ; 06 (79) ; 05 (79) ; 04 (79) ; 03 (79) ; 02 (79) ; 01 (79) ; 12 (67) ; 11 (67) ; 10 (67) ; 09 (67)
- Libelle_activite_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Activité
   Format / valeurs indicatives : Accession / Locatif / Lot
   Exemples : Locatif
   Valeurs observées (effectif) : Locatif (900)
- Libelle_usage_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Usage
   Format / valeurs indicatives : Foyer / Panneau publicitaire / Commerce / Terrain / Autre / Dépendance / Espace commun / Logement / Stationnement
   Exemples : Logement
   Valeurs observées (effectif) : Logement (900)
- Code_nature_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Nature (code)
   Format / valeurs indicatives : Mêmes codes que Lot.Code_nature_lot, plus LAC
   Exemples : LOG
   Valeurs observées (effectif) : LOG (900)
- Libelle_nature_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Nature (libellé)
   Format / valeurs indicatives : Mêmes libellés que Lot.Libelle_nature_lot (+ « locatif »)
   Exemples : Logement
   Valeurs observées (effectif) : Logement (900)
- Code_partie_commune_privative — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Partie privative/commune
   Format / valeurs indicatives : P / C
   Exemples : P
   Valeurs observées (effectif) : P (900)
- Libelle_partie_commune_privative — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Libellé
   Format / valeurs indicatives : Partie commune / Partie privative
   Exemples : Partie privative
   Valeurs observées (effectif) : Partie privative (900)
- Etage — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 6.
   Description : Étage
   Format / valeurs indicatives : -2 à 19
   Exemples : 0 ; 1 ; 2
   Valeurs observées (effectif) : 3 (151) ; 2 (151) ; 1 (151) ; 0 (151) ; 5 (148) ; 4 (148)
- Numero_porte — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 5.
   Confidentialité : RGPD
   Description : Numéro de porte
   Format / valeurs indicatives : PP24 / G56 / 9117 / 2C / L17
   Exemples : PP24 ; G56 ; 9117
   Valeurs observées (effectif) : PP24 (180) ; L17 (180) ; G56 (180) ; 9117 (180) ; 2C (180)
- Code_individuel_collectif — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Individuel/collectif (code)
   Format / valeurs indicatives : MIX / COL / IND
   Exemples : IND
   Valeurs observées (effectif) : IND (900)
- Libelle_individuel_collectif — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Libellé
   Format / valeurs indicatives : Collectif / Individuel / (Individuel/collectif)
   Exemples : Individuel
   Valeurs observées (effectif) : Individuel (900)
- Code_categorie_financement — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 3.
   Description : Financement (code)
   Format / valeurs indicatives : Mêmes codes que Lot
   Exemples : PLUS ; PLAI ; PLS
   Valeurs observées (effectif) : PLUS (302) ; PLS (299) ; PLAI (299)
- Libelle_categorie_financement — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 3.
   Description : Financement (libellé)
   Format / valeurs indicatives : Mêmes libellés que Lot
   Exemples : PLUS ; PLAI ; PLS
   Valeurs observées (effectif) : PLUS (302) ; PLS (299) ; PLAI (299)
- Code_type_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Type de lot (code)
   Format / valeurs indicatives : Mêmes codes que Lot (sous-ensemble)
   Exemples : APP
   Valeurs observées (effectif) : APP (900)
- Libelle_type_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Type de lot (libellé)
   Format / valeurs indicatives : Mêmes libellés que Lot
   Exemples : Appartement
   Valeurs observées (effectif) : Appartement (900)
- Indicateur_accessibilite_PMR — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Accessible PMR
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (600) ; Oui (300)
- Code_niveau_adaptation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 4.
   Description : Niveau d'adaptation
   Format / valeurs indicatives : NA0–NA3 / AH0–AH3 / A0–A3 / A+0–A+3 / HN1 / HN2 / PA2
   Exemples : NA0 ; AH1 ; A2
   Valeurs observées (effectif) : PA2 (225) ; NA0 (225) ; AH1 (225) ; A2 (225)
- Surface_habitable — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 90.
   Description : Surface habitable
   Exemples : 35 ; 36 ; 37
   Plage observée : 35 à 124
- Nombre_chambres — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 4.
   Description : Nombre de chambres
   Exemples : 1 ; 2 ; 3
   Valeurs observées (effectif) : 4 (225) ; 3 (225) ; 2 (225) ; 1 (225)
- Date_construction — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 80.
   Description : Construction
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 1970-01-01 ; 1971-02-04 ; 1972-03-07
   Format observé : AAAA-MM-JJ
- Date_reception_travaux — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 10.
   Description : Réception des travaux
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-06-15 ; 2011-06-15 ; 2012-06-15
   Valeurs observées (effectif) : 2019-06-15 (90) ; 2018-06-15 (90) ; 2017-06-15 (90) ; 2016-06-15 (90) ; 2015-06-15 (90) ; 2014-06-15 (90) ; 2013-06-15 (90) ; 2012-06-15 (90) ; 2011-06-15 (90) ; 2010-06-15 (90)
- Date_livraison — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 10.
   Description : Livraison
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-09-01 ; 2011-09-01 ; 2012-09-01
   Valeurs observées (effectif) : 2019-09-01 (90) ; 2018-09-01 (90) ; 2017-09-01 (90) ; 2016-09-01 (90) ; 2015-09-01 (90) ; 2014-09-01 (90) ; 2013-09-01 (90) ; 2012-09-01 (90) ; 2011-09-01 (90) ; 2010-09-01 (90)
- Date_declaration_achevement_travaux — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 10.
   Description : Déclaration d'achèvement des travaux
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-11-30 ; 2011-11-30 ; 2012-11-30
   Valeurs observées (effectif) : 2019-11-30 (90) ; 2018-11-30 (90) ; 2017-11-30 (90) ; 2016-11-30 (90) ; 2015-11-30 (90) ; 2014-11-30 (90) ; 2013-11-30 (90) ; 2012-11-30 (90) ; 2011-11-30 (90) ; 2010-11-30 (90)
- Date_mise_en_service — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 10.
   Description : Mise en service
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-10-01 ; 2011-10-01 ; 2012-10-01
   Valeurs observées (effectif) : 2019-10-01 (90) ; 2018-10-01 (90) ; 2017-10-01 (90) ; 2016-10-01 (90) ; 2015-10-01 (90) ; 2014-10-01 (90) ; 2013-10-01 (90) ; 2012-10-01 (90) ; 2011-10-01 (90) ; 2010-10-01 (90)
- Nombre_jours_depuis_mise_en_service — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 10.
   Description : Jours depuis la mise en service
   Exemples : 5851 ; 5486 ; 5120
   Valeurs observées (effectif) : 5851 (90) ; 5486 (90) ; 5120 (90) ; 4755 (90) ; 4390 (90) ; 4025 (90) ; 3659 (90) ; 3294 (90) ; 2929 (90) ; 2564 (90)
- Date_debut_commercialisation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 10.
   Description : Début de commercialisation
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2010-10-15 ; 2011-10-15 ; 2012-10-15
   Valeurs observées (effectif) : 2019-10-15 (90) ; 2018-10-15 (90) ; 2017-10-15 (90) ; 2016-10-15 (90) ; 2015-10-15 (90) ; 2014-10-15 (90) ; 2013-10-15 (90) ; 2012-10-15 (90) ; 2011-10-15 (90) ; 2010-10-15 (90)
- Code_etat — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : État (code)
   Format / valeurs indicatives : AVA / ACO / VCO / VP / RRE / MES / LO / VDB / HS / MDG / TRX / VDE / VTE / NLO / VRE / VVT / FBE / VDO / VRD / NULL / ATD / MEL / VCT / DML
   Exemples : OCC
   Valeurs observées (effectif) : OCC (900)
- Libelle_etat — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : État (libellé)
   Format / valeurs indicatives : Vacance détachement STN / Vacance réservée / Vacance Remise à Dispo / Vacance pour travaux / Attente démolition / Vendu / Att. valid. affectation / vendu à autre bailleur / Fin bail emphytéotique / Hors service / Attente de vente / Mise en location (neuf) / Projet réhabilitation / UG non louée (Agc/siège) / vendu à l'occupant / Vacance partielle / Location ordinaire / Vacance ordinaire / Arret commercialisation / démolition / Vacances territoires / Donné Mandat de Gestion / Mise en service / NULL
   Exemples : Occupe
   Valeurs observées (effectif) : Occupe (900)
- Indicateur_changement_etat — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Changement d'état dans le mois
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (900)
- Nombre_changement_etat_annee_N — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Changements d'état, année N
   Exemples : 0
   Valeurs observées (effectif) : 0 (900)
- Nombre_changement_etat_12_derniers_mois — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Changements d'état, 12 derniers mois
   Exemples : 0
   Valeurs observées (effectif) : 0 (900)
- Indicateur_exploitation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : En exploitation
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (900)
- Indicateur_disponibilite_commercialisation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Disponible à la commercialisation
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (900)
- Indicateur_propriete — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 1.
   Description : Lot en propriété
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (900)
- Nombre_entree — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 3.
   Description : Entrées
   Exemples : 0 ; 1 ; 2
   Valeurs observées (effectif) : 2 (300) ; 1 (300) ; 0 (300)
- Nombre_entree_annee_N — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Entrées, année N
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_entree_12_derniers_mois — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 3.
   Description : Entrées, 12 derniers mois
   Exemples : 0 ; 1 ; 2
   Valeurs observées (effectif) : 2 (300) ; 1 (300) ; 0 (300)
- Nombre_sortie — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Sorties
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_sortie_annee_N — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Sorties, année N
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_sortie_12_derniers_mois — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Sorties, 12 derniers mois
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_entree_mutation — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Entrées par mutation
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_entree_mutation_annee_N — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Entrées par mutation, année N
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_entree_mutation_12_derniers_moi — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 900.
   Description : Entrées par mutation, 12 derniers mois (nom tronqué dans le PDF)
   Exemples : 1 ; 2 ; 3
   Plage observée : 1 à 900
- Nombre_sortie_mutation — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Sorties par mutation
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_sortie_mutation_annee_N — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Sorties par mutation, année N
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_sortie_mutation_12_derniers_mois — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 2.
   Description : Sorties par mutation, 12 derniers mois
   Exemples : 0 ; 1
   Valeurs observées (effectif) : 1 (450) ; 0 (450)
- Nombre_jours_vacance — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 30.
   Description : Jours de vacance
   Exemples : 0 ; 1 ; 2
   Plage observée : 0 à 29
- Nombre_jours_vacance_annee_N — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 20.
   Description : Jours de vacance, année N
   Exemples : 0 ; 1 ; 2
   Plage observée : 0 à 19
- Nombre_jours_vacance_12_derniers_mois — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 20.
   Description : Jours de vacance, 12 derniers mois
   Exemples : 0 ; 1 ; 2
   Plage observée : 0 à 19
- Montant_perte_financiere — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 500.
   Description : Perte financière
   Exemples : 0 ; 1 ; 2
   Plage observée : 0 à 499
- Montant_perte_financiere_annee_N — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 300.
   Description : Perte financière, année N
   Exemples : 0 ; 1 ; 2
   Plage observée : 0 à 299
- Montant_perte_financiere_12_derniers_mois — Type SQLite : INTEGER. NULL observés : non (0/900). Valeurs distinctes non NULL : 600.
   Description : Perte financière, 12 derniers mois
   Exemples : 0 ; 1 ; 2
   Plage observée : 0 à 599
- Lien_IKOS_synthese_lot — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Lien IKOS
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/lot/AJ-000001 ; https://ikos.local/lot/AC-000002 ; https://ikos.local/lot/BSH-000003
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/900). Valeurs distinctes non NULL : 731.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Occupant
Nombre de lignes : 400
- ID_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Identifiant
   Format / valeurs indicatives : Code_societe-Code_occupant (AC-000022769)
   Exemples : AJ-003301-OCC-0001 ; AC-003302-OCC-0002 ; BSH-003303-OCC-0003
- ID_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Client de rattachement
   Format / valeurs indicatives : AC-003301
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (100) ; BSH (100) ; AJ (100) ; AC (100)
- Code_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Code client
   Format / valeurs indicatives : 6 chiffres
   Exemples : 003301 ; 003302 ; 003303
   Format observé : 999999 (ex. 003301)
- Code_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Code occupant
   Format / valeurs indicatives : 9 chiffres
   Exemples : O000001 ; O000002 ; O000003
   Format observé : A999999 (ex. O000001)
- Date_debut_rattachement_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Début de rattachement
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2018-01-01 ; 2019-02-03 ; 2020-03-05
   Format observé : AAAA-MM-JJ
- Date_fin_rattachement_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Confidentialité : RGPD
   Description : Fin de rattachement
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-12-31 ; 2099-12-31
   Valeurs observées (effectif) : 2099-12-31 (320) ; 2025-12-31 (80)
- Indicateur_rattachement_client — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Rattaché au client
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Indicateur_rattachement_menage — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Rattaché au ménage
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Qualification_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Qualification
   Format / valeurs indicatives : Contactant / Occupant
   Exemples : Occupant
   Valeurs observées (effectif) : Occupant (400)
- Indicateur_rattachement_fiscal — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Rattachement fiscal
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Indicateur_garde_alternee — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Garde alternée
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Indicateur_droit_de_visite — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Confidentialité : RGPD
   Description : Droit de visite
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (266) ; Oui (134)
- Indicateur_carte_mobilite_inclusion — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Carte mobilité inclusion
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (400)
- Type_personne — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Type de personne
   Format / valeurs indicatives : Physique / Morale
   Exemples : Physique
   Valeurs observées (effectif) : Physique (400)
- Code_forme_juridique_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Forme juridique (code)
   Format / valeurs indicatives : 2 à 4 lettres majuscules
   Exemples : PHYS
   Valeurs observées (effectif) : PHYS (400)
- Libelle_forme_juridique_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Forme juridique (voir *Points d'attention*)
   Format / valeurs indicatives : Monsieur / Madame / Maire / Entreprise / Agence / SARL / SCCV / Société
   Exemples : Monsieur ; Madame ; Maire
   Valeurs observées (effectif) : Monsieur (134) ; Maire (133) ; Madame (133)
- Libelle_titre_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Titre/raison (voir *Points d'attention*)
   Format / valeurs indicatives : ST AVE CASSIOPEE, MAIRIE CLÉGUER, BOTREL SAS
   Exemples : Monsieur ; Madame ; Mademois.
   Valeurs observées (effectif) : Monsieur (134) ; Mademois. (133) ; Madame (133)
- Raison_sociale_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Voir *Points d'attention*
   Format / valeurs indicatives : MR / MME / MLLE / STE
   Exemples : MR ; MME ; MLLE
   Valeurs observées (effectif) : MR (134) ; MME (133) ; MLLE (133)
- Code_titre_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Voir *Points d'attention*
   Format / valeurs indicatives : Monsieur / Madame / Mademois. / Société
   Exemples : Monsieur ; Madame ; Mademois.
   Valeurs observées (effectif) : Monsieur (134) ; Mademois. (133) ; Madame (133)
- Nom_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 16.
   Confidentialité : RGPD
   Description : Nom
   Exemples : MARTIN ; BERNARD ; DUBOIS
   Valeurs observées (effectif) : THOMAS (25) ; SIMON (25) ; ROBERT (25) ; RICHARD (25) ; PETIT (25) ; MOREAU (25) ; MICHEL (25) ; MARTIN (25) ; LEROY (25) ; LEFEVRE (25) ; LAURENT (25) ; GARCIA (25) ; DURAND (25) ; DUBOIS (25) ; DAVID (25) ; BERNARD (25)
- Prenom_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 16.
   Confidentialité : RGPD
   Description : Prénom
   Exemples : Jean ; Marie ; Lucas
   Valeurs observées (effectif) : Thomas (25) ; Sarah (25) ; Paul (25) ; Nicolas (25) ; Marie (25) ; Manon (25) ; Lucas (25) ; Louis (25) ; Lea (25) ; Julie (25) ; Jean (25) ; Hugo (25) ; Emma (25) ; Chloe (25) ; Camille (25) ; Antoine (25)
- Age_occupant — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 46.
   Confidentialité : RGPD
   Description : Âge
   Format / valeurs indicatives : 1 à 150
   Exemples : 56 ; 55 ; 54
   Plage observée : 11 à 90
- Classe_age_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Confidentialité : RGPD
   Description : Tranche d'âge
   Format / valeurs indicatives : 18 ans et moins / 18-29 ans / 30-44 ans / 45-64 ans / 65 ans et plus / NULL
   Exemples : 30-44 ans ; 18-29 ans ; 18 ans et moins
   Valeurs observées (effectif) : 18 ans et moins (164) ; 18-29 ans (112) ; 30-44 ans (65) ; 65 ans et plus (59)
- Majorite_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Confidentialité : RGPD
   Description : Majeur
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Oui (349) ; Non (51)
- Date_naissance_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Naissance
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 1970-01-01 ; 1971-02-03 ; 1972-03-05
   Format observé : AAAA-MM-JJ
- Date_deces_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Décès
   Format / valeurs indicatives : AAAA-MM-JJ ou NULL
   Exemples : 2099-12-31
   Valeurs observées (effectif) : 2099-12-31 (400)
- Sexe_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Confidentialité : RGPD
   Description : Sexe
   Format / valeurs indicatives : M / F
   Exemples : M ; F
   Valeurs observées (effectif) : M (200) ; F (200)
- Indicateur_revenus_imposables_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Revenus imposables connus
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (400)
- Annee_revenus_imposables_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 1.
   Confidentialité : RGPD
   Description : Année des revenus
   Format / valeurs indicatives : AAAA
   Exemples : 2025-01-01
   Valeurs observées (effectif) : 2025-01-01 (400)
- Montant_revenus_imposables_occupant — Type SQLite : INTEGER. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Confidentialité : RGPD
   Description : Montant des revenus imposables
   Exemples : 18000 ; 18001 ; 18002
   Plage observée : 18000 à 18399
- Situation_famille_occupant — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Confidentialité : RGPD
   Description : Situation familiale
   Format / valeurs indicatives : Union libre - concubin / Pacsé(e) / Veuf(ve) / Célibataire / Divorcé(e) / Marié(e) / Séparé(e) / NULL
   Exemples : Célibataire ; Marié(e) ; Pacsé(e)
   Valeurs observées (effectif) : Pacsé(e) (100) ; Marié(e) (100) ; Divorcé(e) (100) ; Célibataire (100)
- Libelle_detail_lien_rattachement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Confidentialité : RGPD
   Description : Lien de rattachement
   Format / valeurs indicatives : Enfant / Pacsé(e) / Parent / Colocataire / A charge / Autres (colocataire…) / Conjoint / Concubin
   Exemples : Conjoint ; Enfant ; Parent
   Valeurs observées (effectif) : Parent (100) ; Enfant (100) ; Conjoint (100) ; Colocataire (100)
- Code_occupant_de_rattachement — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 50.
   Confidentialité : RGPD
   Description : Occupant de référence
   Format / valeurs indicatives : 9 chiffres
   Exemples : O000001 ; O000002 ; O000003
   Format observé : A999999 (ex. O000001)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

- Telephone_occupant — Type SQLite : TEXT.
   Confidentialité : RGPD
   Description : Numéro de téléphone de l'occupant. Colonne présente dans SQLite, ajoutée à la documentation après contrôle du schéma.
- Mail_occupant — Type SQLite : TEXT.
   Confidentialité : RGPD
   Description : Adresse e-mail de l'occupant. Colonne présente dans SQLite, ajoutée à la documentation après contrôle du schéma.

## Organisation
Nombre de lignes : 30
- ID_organisation — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Description : Identifiant
   Format / valeurs indicatives : AC-R2-01-08
   Exemples : AJ-R1-01-01 ; AC-R2-02-02 ; BSH-R3-03-03
- Niveau_organisation — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 1.
   Description : Niveau hiérarchique
   Format / valeurs indicatives : Niveau 1 / Niveau 2 / Niveau 3
   Exemples : Niveau 3
   Valeurs observées (effectif) : Niveau 3 (30)
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : AJ (8) ; AC (8) ; MF1 (7) ; BSH (7)
- Code_niveau_organisation_1 — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 8.
   Description : Niveau 1
   Format / valeurs indicatives : 2 à 4 caractères
   Exemples : R1 ; R2 ; R3
   Valeurs observées (effectif) : R6 (4) ; R5 (4) ; R4 (4) ; R3 (4) ; R2 (4) ; R1 (4) ; R8 (3) ; R7 (3)
- Code_niveau_organisation_2 — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 9.
   Description : Niveau 2
   Format / valeurs indicatives : 01 / 02 / 03 / 04 / 05 / 09 / BR
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 03 (4) ; 02 (4) ; 01 (4) ; 09 (3) ; 08 (3) ; 07 (3) ; 06 (3) ; 05 (3) ; 04 (3)
- Code_niveau_organisation_3 — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 12.
   Description : Niveau 3
   Format / valeurs indicatives : 01 … 09 / 11 / 12
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 06 (3) ; 05 (3) ; 04 (3) ; 03 (3) ; 02 (3) ; 01 (3) ; 12 (2) ; 11 (2) ; 10 (2) ; 09 (2) ; 08 (2) ; 07 (2)
- Libelle_organisation — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Description : Libellé
   Format / valeurs indicatives : AIGUILLON Brest
   Exemples : Agence Rennes 1 ; Agence Nantes 2 ; Agence Brest 3
- Adresse — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Confidentialité : RGPD
   Description : Adresse
   Format / valeurs indicatives : Agence Brest
   Exemples : 10 RUE DES HORTENSIAS ; 11 RUE DES HORTENSIAS ; 12 RUE DES HORTENSIAS
- Indicateur_validite — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 1.
   Description : Organisation valide
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui
   Valeurs observées (effectif) : Oui (30)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/30). Valeurs distinctes non NULL : 30.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Organisation_patrimoine_pivot
Nombre de lignes : 80
- ID_organisation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 30.
   Description : Organisation
   Format / valeurs indicatives : AC-R2-01-08
   Exemples : AJ-R1-01-01 ; AC-R2-02-02 ; BSH-R3-03-03
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Patrimoine
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Patrimoine
Nombre de lignes : 80
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Identifiant
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- ID_organisation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 30.
   Description : Organisation de gestion
   Format / valeurs indicatives : AC-R2-01-08
   Exemples : AJ-R1-01-01 ; AC-R2-02-02 ; BSH-R3-03-03
- Niveau_patrimoine — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 1.
   Description : Niveau
   Format / valeurs indicatives : Bâtiment / Stationnement / Cage d'escalier / Résidence
   Exemples : Résidence
   Valeurs observées (effectif) : Résidence (80)
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (20) ; BSH (20) ; AJ (20) ; AC (20)
- Code_niveau_patrimoine_1 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Niveau 1
   Format / valeurs indicatives : 3 ou 4 caractères
   Exemples : AJ01 ; AC02 ; BS03
   Format observé : AA99 (ex. AJ01)
- Code_niveau_patrimoine_2 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 9.
   Description : Niveau 2
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (9) ; 07 (9) ; 06 (9) ; 05 (9) ; 04 (9) ; 03 (9) ; 02 (9) ; 01 (9) ; 09 (8)
- Code_niveau_patrimoine_3 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 12.
   Description : Niveau 3
   Format / valeurs indicatives : 1 à 3 caractères
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 08 (7) ; 07 (7) ; 06 (7) ; 05 (7) ; 04 (7) ; 03 (7) ; 02 (7) ; 01 (7) ; 12 (6) ; 11 (6) ; 10 (6) ; 09 (6)
- Libelle_patrimoine — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Libellé
   Format / valeurs indicatives : Cellule A. Guérin, Les Orchidées bât. C
   Exemples : Residence 001 ; Residence 002 ; Residence 003
- Code_niveau_organisation_1 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 8.
   Description : Organisation niveau 1
   Format / valeurs indicatives : 2 à 4 caractères
   Exemples : R1 ; R2 ; R3
   Valeurs observées (effectif) : R4 (11) ; R3 (11) ; R2 (11) ; R1 (11) ; R6 (10) ; R5 (10) ; R8 (8) ; R7 (8)
- Code_niveau_organisation_2 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 9.
   Description : Organisation niveau 2
   Format / valeurs indicatives : 01 / 02 / 03 / 04 / 05 / 09 / BR
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 02 (11) ; 01 (11) ; 03 (10) ; 09 (8) ; 08 (8) ; 07 (8) ; 06 (8) ; 05 (8) ; 04 (8)
- Code_niveau_organisation_3 — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 12.
   Description : Organisation niveau 3
   Format / valeurs indicatives : 01 … 09 / 11 / 12
   Exemples : 01 ; 02 ; 03
   Valeurs observées (effectif) : 06 (8) ; 05 (8) ; 04 (8) ; 03 (8) ; 02 (8) ; 01 (8) ; 08 (6) ; 07 (6) ; 12 (5) ; 11 (5) ; 10 (5) ; 09 (5)
- Libelle_organisation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 30.
   Description : Libellé de l'organisation
   Format / valeurs indicatives : AIGUILLON Brest
   Exemples : Agence Rennes 1 ; Agence Nantes 2 ; Agence Brest 3
- Adresse_complete — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Adresse complète
   Format / valeurs indicatives : 4 Rue des epinettes 44115 Haute-Goulaine
   Exemples : 20 RUE DU PORT ; 21 RUE DU PORT ; 22 RUE DU PORT
- Adresse — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Adresse (rue)
   Format / valeurs indicatives : 4 Rue des epinettes
   Exemples : 20 RUE DU PORT ; 21 RUE DU PORT ; 22 RUE DU PORT
- Libelle_commune — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 5.
   Description : Commune
   Format / valeurs indicatives : RENNES, BOUAYE
   Exemples : RENNES ; NANTES ; BREST
   Valeurs observées (effectif) : VANNES (16) ; RENNES (16) ; NANTES (16) ; LORIENT (16) ; BREST (16)
- Code_postal — Type SQLite : INTEGER. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Code postal
   Format / valeurs indicatives : 5 chiffres (35160)
   Exemples : 35000 ; 35001 ; 35002
   Plage observée : 35000 à 35079
- Code_INSEE_commune — Type SQLite : INTEGER. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Code INSEE
   Format / valeurs indicatives : 5 chiffres (56118)
   Exemples : 35000 ; 35001 ; 35002
   Plage observée : 35000 à 35079
- Latitude — Type SQLite : REAL. NULL observés : non (0/80). Valeurs distinctes non NULL : 20.
   Confidentialité : RGPD
   Description : Latitude
   Format / valeurs indicatives : 48.109781
   Exemples : 47.2 ; 47.21 ; 47.22
   Plage observée : 47.2 à 47.39
- Longitude — Type SQLite : REAL. NULL observés : non (0/80). Valeurs distinctes non NULL : 20.
   Confidentialité : RGPD
   Description : Longitude
   Format / valeurs indicatives : -1.668032
   Exemples : -1.6 ; -1.59 ; -1.58
   Plage observée : -1.6 à -1.41
- Code_département — Type SQLite : INTEGER. NULL observés : non (0/80). Valeurs distinctes non NULL : 5.
   Description : Département
   Exemples : 35 ; 36 ; 37
   Valeurs observées (effectif) : 39 (16) ; 38 (16) ; 37 (16) ; 36 (16) ; 35 (16)
- Code_bassin_habitat — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 6.
   Description : Bassin d'habitat
   Format / valeurs indicatives : 3 lettres majuscules
   Exemples : B01 ; B02 ; B03
   Valeurs observées (effectif) : B02 (14) ; B01 (14) ; B06 (13) ; B05 (13) ; B04 (13) ; B03 (13)
- Code_quartier — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 20.
   Description : Quartier
   Format / valeurs indicatives : NULL
   Exemples : Q01 ; Q02 ; Q03
   Format observé : A99 (ex. Q01)
- Date_construction — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Construction
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 1970-01-01 ; 1971-02-04 ; 1972-03-07
   Format observé : AAAA-MM-JJ
- Mode_acquisition — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 4.
   Description : Mode d'acquisition
   Format / valeurs indicatives : Construction par l'organisme / Acquisition avec travaux / Acquisition sans travaux / Acquisition en VEFA
   Exemples : Construction par l'organisme ; Acquisition avec travaux ; Acquisition sans travaux
   Valeurs observées (effectif) : Construction par l'organisme (20) ; Acquisition sans travaux (20) ; Acquisition en VEFA (20) ; Acquisition avec travaux (20)
- Date_acquisition — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Acquisition
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2000-01-01 ; 2001-02-03 ; 2002-03-05
   Format observé : AAAA-MM-JJ
- Indicateur_annulation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 1.
   Description : Annulé
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (80)
- Date_fin_validite — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 1.
   Description : Fin de validité
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2099-12-31
   Valeurs observées (effectif) : 2099-12-31 (80)
- Lien_IKOS_synthese_patrimoine — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Lien IKOS
   Format / valeurs indicatives : https://…
   Exemples : https://ikos.local/patrimoine/AJ-AJ01-01-01 ; https://ikos.local/patrimoine/AC-AC02-02-02 ; https://ikos.local/patrimoine/BSH-BS03-03-03
- Lien_Google_Maps — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 20.
   Confidentialité : RGPD
   Description : Lien Google Maps
   Format / valeurs indicatives : https://…
   Exemples : https://maps.google.com/?q=47.2,-1.6 ; https://maps.google.com/?q=47.21,-1.59 ; https://maps.google.com/?q=47.220000000000006,-1.58
- Lien_Google_Earth — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Confidentialité : RGPD
   Description : Lien Google Earth
   Format / valeurs indicatives : https://…
   Exemples : https://earth.google.com/p/AJ-AJ01-01-01 ; https://earth.google.com/p/AC-AC02-02-02 ; https://earth.google.com/p/BSH-BS03-03-03
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/80). Valeurs distinctes non NULL : 80.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Patrimoine_lot_pivot
Nombre de lignes : 400
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- ID_patrimoine — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 80.
   Description : Patrimoine
   Format / valeurs indicatives : AC-0789-01-02
   Exemples : AJ-AJ01-01-01 ; AC-AC02-02-02 ; BSH-BS03-03-03
- ID_patrimoine_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Clé de jointure avec Equipement
   Format / valeurs indicatives : Format ID_lot ou ID_patrimoine
   Exemples : AJ-AJ01-01-01-AJ-000001 ; AC-AC02-02-02-AC-000002 ; BSH-BS03-03-03-BSH-000003
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Piece
Nombre de lignes : 250
- ID_piece — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Identifiant
   Format / valeurs indicatives : Code_societe-Code_lot-Code_piece (AC-001286-CUI)
   Exemples : AJ-000001-P-0001 ; AC-000002-P-0002 ; BSH-000003-P-0003
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : AJ (63) ; AC (63) ; MF1 (62) ; BSH (62)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Code lot
   Format / valeurs indicatives : 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Code_piece — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 5.
   Description : Code de la pièce
   Format / valeurs indicatives : CH1–CH5, SEJ, SDB, CUI, AUT, WC…
   Exemples : SEJ ; CUI ; CH1
   Valeurs observées (effectif) : WC (50) ; SEJ (50) ; SDB (50) ; CUI (50) ; CH1 (50)
- Libelle_piece — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 5.
   Description : Libellé
   Format / valeurs indicatives : Chambre 1–5, Séjour, Salle de bain, Cuisine, Autres, WC…
   Exemples : Sejour ; Cuisine ; Chambre
   Valeurs observées (effectif) : WC (50) ; Sejour (50) ; Salle de bain (50) ; Cuisine (50) ; Chambre (50)
- Libelle_categorie_piece — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 2.
   Description : Catégorie
   Format / valeurs indicatives : Chambre, Circulation, Salle de bain, WC, Séjour, Annexe extérieure, Annexe intérieure, Autres, Cuisine
   Exemples : Piece principale ; Piece de service
   Valeurs observées (effectif) : Piece principale (125) ; Piece de service (125)
- Surface_reelle — Type SQLite : INTEGER. NULL observés : non (0/250). Valeurs distinctes non NULL : 30.
   Description : Surface réelle
   Exemples : 8 ; 9 ; 10
   Plage observée : 8 à 37
- Surface_corrigee — Type SQLite : REAL. NULL observés : non (0/250). Valeurs distinctes non NULL : 30.
   Description : Surface corrigée
   Exemples : 8.5 ; 9.5 ; 10.5
   Plage observée : 8.5 à 37.5
- Surface_reduite — Type SQLite : INTEGER. NULL observés : non (0/250). Valeurs distinctes non NULL : 25.
   Description : Surface réduite
   Exemples : 7 ; 8 ; 9
   Plage observée : 7 à 31
- Code_type_decompte — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 2.
   Description : Type de décompte de surface
   Format / valeurs indicatives : SUT / SCO
   Exemples : SUT ; SCO
   Valeurs observées (effectif) : SUT (125) ; SCO (125)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/250). Valeurs distinctes non NULL : 250.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Reglementation
Nombre de lignes : 400
- ID_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Lot
   Format / valeurs indicatives : AC-001752
   Exemples : AJ-000001 ; AC-000002 ; BSH-000003
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : MF1 (100) ; BSH (100) ; AJ (100) ; AC (100)
- Code_lot — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Code lot
   Format / valeurs indicatives : 6 chiffres
   Exemples : 000001 ; 000002 ; 000003
   Format observé : 999999 (ex. 000001)
- Type_reglementation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 7.
   Description : Réglementation
   Format / valeurs indicatives : DPE / EIIG / RAAT ST / DTA / EIIE / DAPP / CREP
   Exemples : DPE ; EIIG ; RAAT ST
   Valeurs observées (effectif) : DPE (58) ; RAAT ST (57) ; EIIG (57) ; EIIE (57) ; DTA (57) ; DAPP (57) ; CREP (57)
- Eligibilite — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 2.
   Description : Lot soumis à la réglementation
   Format / valeurs indicatives : Oui / Non
   Exemples : Non ; Oui
   Valeurs observées (effectif) : Oui (320) ; Non (80)
- Etat_conformite_reglementaire — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 3.
   Description : État de conformité
   Format / valeurs indicatives : Valide / Non valide / Non requis
   Exemples : Valide ; Non valide ; Non requis
   Valeurs observées (effectif) : Valide (134) ; Non valide (133) ; Non requis (133)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/400). Valeurs distinctes non NULL : 400.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff

## Releve_compte_client_historique
### Identification
Nombre de lignes : 709
- ID_client — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Client
   Format / valeurs indicatives : AC-003301
   Exemples : AJ-003301 ; AC-003302 ; BSH-003303
- ID_client_annee_mois — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 709.
   Confidentialité : RGPD
   Description : Client et mois
   Format / valeurs indicatives : AC-003193-2020-08
   Exemples : AJ-003301-2025-01 ; AC-003302-2025-01 ; BSH-003303-2025-01
- Annee_mois — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 3.
   Description : Mois
   Format / valeurs indicatives : AAAA-MM
   Exemples : 2025-01-01 ; 2025-02-01 ; 2025-03-01
   Valeurs observées (effectif) : 2025-02-01 (320) ; 2025-01-01 (320) ; 2025-03-01 (69)
- Annee_mois_ordre — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 365.
   Description : Mois, format de tri
   Format / valeurs indicatives : AAAA-MM (le PDF ne précise pas le format AAAAMM)
   Exemples : 2025-01-01 ; 2025-01-02 ; 2025-01-03
   Format observé : AAAA-MM-JJ
- Code_societe — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 4.
   Description : Société
   Format / valeurs indicatives : AJ / AC / BSH / MF1
   Exemples : AJ ; AC ; BSH
   Valeurs observées (effectif) : AJ (178) ; MF1 (177) ; BSH (177) ; AC (177)
- Code_client — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 320.
   Confidentialité : RGPD
   Description : Code client
   Format / valeurs indicatives : 6 chiffres
   Exemples : 003301 ; 003302 ; 003303
   Format observé : 999999 (ex. 003301)
- Montant_solde_client — Type SQLite : REAL. NULL observés : non (0/709). Valeurs distinctes non NULL : 30.
   Description : Solde du compte
   Exemples : -355.0 ; -319.5 ; -284.0
   Plage observée : -355.0 à 674.5
- Date_ecriture_retenue_solde_client — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 3.
   Description : Date de l'écriture retenue pour le solde
   Format / valeurs indicatives : AAAA-MM-JJ
   Exemples : 2025-01-16 ; 2025-02-16 ; 2025-03-16
   Valeurs observées (effectif) : 2025-02-16 (320) ; 2025-01-16 (320) ; 2025-03-16 (69)
- Numero_ecriture_retenue_solde_client — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 709.
   Description : Numéro de l'écriture retenue
   Format / valeurs indicatives : 1 à 10 000
   Exemples : 1 ; 2 ; 3
   Plage observée : 1 à 709
- Montant_impaye_potentiel — Type SQLite : REAL. NULL observés : non (0/709). Valeurs distinctes non NULL : 20.
   Description : Impayé potentiel
   Exemples : 0.0 ; 35.5 ; 71.0
   Plage observée : 0.0 à 674.5
- Classe_montant_impaye_potentiel — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 5.
   Description : Tranche
   Format / valeurs indicatives : Pas de dette / 0-10€ / 10-150€ / 150-600€ / 600-1500€ / 1500-3000€ / 3000-4500€ / > 4500€
   Exemples : Pas de dette ; 0-10€ ; 10-150€
   Valeurs observées (effectif) : Pas de dette (142) ; 150-600€ (142) ; 10-150€ (142) ; 0-10€ (142) ; 600-1500€ (141)
- Montant_sommes_attente — Type SQLite : REAL. NULL observés : non (0/709). Valeurs distinctes non NULL : 100.
   Description : Sommes en attente
   Exemples : 0.0 ; 2.5 ; 5.0
   Plage observée : 0.0 à 247.5
- Montant_impaye_retardataire — Type SQLite : REAL. NULL observés : non (0/709). Valeurs distinctes non NULL : 20.
   Description : Impayé retardataire
   Exemples : 0.0 ; 17.75 ; 35.5
   Plage observée : 0.0 à 337.25
- Montant_impaye — Type SQLite : REAL. NULL observés : non (0/709). Valeurs distinctes non NULL : 20.
   Description : Impayé
   Exemples : 0.0 ; 35.5 ; 71.0
   Plage observée : 0.0 à 674.5
- Classe_montant_impaye — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 4.
   Description : Tranche d'impayé
   Format / valeurs indicatives : Mêmes tranches que ci-dessus
   Exemples : Pas de dette ; 0-10€ ; 10-150€
   Valeurs observées (effectif) : Pas de dette (178) ; 150-600€ (177) ; 10-150€ (177) ; 0-10€ (177)
- Indicateur_anciennete_impaye — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 3.
   Description : Ancienneté de l'impayé
   Format / valeurs indicatives : Pas de dette / Nouveau / Ancien
   Exemples : Pas de dette ; Nouveau ; Ancien
   Valeurs observées (effectif) : Pas de dette (237) ; Nouveau (236) ; Ancien (236)
- Indicateur_evolution_impaye — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 3.
   Description : Tendance
   Format / valeurs indicatives : Baisse / Stable / Hausse
   Exemples : Baisse ; Stable ; Hausse
   Valeurs observées (effectif) : Baisse (237) ; Stable (236) ; Hausse (236)
- Evolution_montant_impaye — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 11.
   Description : Variation de l'impayé
   Exemples : -50 ; -40 ; -30
   Valeurs observées (effectif) : -10 (65) ; -20 (65) ; -30 (65) ; -40 (65) ; -50 (65) ; 50 (64) ; 40 (64) ; 30 (64) ; 20 (64) ; 10 (64) ; 0 (64)
- Montant_loyer — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 200.
   Description : Loyer
   Exemples : 450 ; 451 ; 452
   Plage observée : 450 à 649
- Montant_loyer_residuel_hors_rappel_APL_RLS — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 150.
   Description : Loyer résiduel hors rappel APL/RLS
   Exemples : 300 ; 301 ; 302
   Plage observée : 300 à 449
- Indicateur_evolution_loyer_residuel_hors_rappel_APL_RLS — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 3.
   Description : Tendance
   Format / valeurs indicatives : Baisse / Stable / Hausse
   Exemples : Baisse ; Stable ; Hausse
   Valeurs observées (effectif) : Baisse (237) ; Stable (236) ; Hausse (236)
- Evolution_montant_loyer_residuel_hors_rappel_APL_RLS — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 9.
   Description : Variation
   Exemples : -20 ; -15 ; -10
   Valeurs observées (effectif) : 10 (79) ; 5 (79) ; 0 (79) ; -5 (79) ; -10 (79) ; -15 (79) ; -20 (79) ; 20 (78) ; 15 (78)
- Montant_loyer_residuel_avec_rappel_APL_RLS — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 150.
   Description : Loyer résiduel avec rappel APL/RLS
   Exemples : 280 ; 281 ; 282
   Plage observée : 280 à 429
- Montant_APL — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 51.
   Description : APL
   Exemples : 120 ; 0 ; 123
   Plage observée : 0 à 169
- Indicateur_APL — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Bénéficiaire APL
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (472) ; Oui (237)
- Montant_rappel_APL — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Rappel APL
   Exemples : 50 ; 0
   Valeurs observées (effectif) : 0 (531) ; 50 (178)
- Montant_RLS — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Réduction de loyer de solidarité
   Exemples : 20 ; 0
   Valeurs observées (effectif) : 20 (355) ; 0 (354)
- Montant_rappel_RLS — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Rappel RLS
   Exemples : 15 ; 0
   Valeurs observées (effectif) : 0 (567) ; 15 (142)
- Montant_allocation_logement — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Allocation logement
   Exemples : 80 ; 0
   Valeurs observées (effectif) : 0 (531) ; 80 (178)
- Montant_charges — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 40.
   Description : Charges
   Exemples : 80 ; 81 ; 82
   Plage observée : 80 à 119
- Montant_charges_facturation_client — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 40.
   Description : Charges (facturation client)
   Exemples : 80 ; 81 ; 82
   Plage observée : 80 à 119
- Montant_charges_facturation_immediate — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 30.
   Description : Charges (facturation immédiate)
   Exemples : 70 ; 71 ; 72
   Plage observée : 70 à 99
- Montant_SLS — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Supplément de loyer de solidarité
   Exemples : 35 ; 0
   Valeurs observées (effectif) : 0 (607) ; 35 (102)
- Montant_penalite_SLS — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Pénalité SLS
   Exemples : 5 ; 0
   Valeurs observées (effectif) : 0 (607) ; 5 (102)
- Indicateur_penalite_SLS — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Pénalité SLS appliquée
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (607) ; Oui (102)
- Montant_penalite_assurance — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Pénalité d'assurance
   Exemples : 8 ; 0
   Valeurs observées (effectif) : 0 (590) ; 8 (119)
- Indicateur_mandat_prelevement_quittancement — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Mandat de prélèvement (quittancement)
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Oui (355) ; Non (354)
- Jour_mandat_prelevement_quittancement — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 25.
   Description : Jour de prélèvement (quittancement)
   Format / valeurs indicatives : type non précisé dans le PDF
   Exemples : 5 ; 6 ; 7
   Plage observée : 5 à 29
- Indicateur_mandat_prelevement_accord_reglement — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 1.
   Description : Mandat de prélèvement (accord de règlement)
   Format / valeurs indicatives : Oui / Non
   Exemples : Non
   Valeurs observées (effectif) : Non (709)
- Jour_mandat_prelevement_accord_reglement — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 20.
   Description : Jour de prélèvement (accord de règlement)
   Format / valeurs indicatives : 1 à 30
   Exemples : 10 ; 11 ; 12
   Plage observée : 10 à 29
- Libelle_type_paiement_majoritaire — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 8.
   Description : Moyen de paiement majoritaire
   Format / valeurs indicatives : Carte / TPE / Virement / Chèque / Prélèvement / Ecriture manuelle / Pas de paiement / Espèces
   Exemples : Carte ; TPE ; Virement
   Valeurs observées (effectif) : Virement (89) ; TPE (89) ; Prélèvement (89) ; Chèque (89) ; Carte (89) ; Pas de paiement (88) ; Espèces (88) ; Ecriture manuelle (88)
- Montant_paiement_prelevement — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 100.
   Description : Paiements par prélèvement
   Exemples : 300 ; 301 ; 302
   Plage observée : 300 à 399
- Montant_rejet_prelevement — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Rejets de prélèvement
   Exemples : 30 ; 0
   Valeurs observées (effectif) : 0 (638) ; 30 (71)
- Montant_paiement_virement_bancaire — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 70.
   Description : Paiements par virement
   Exemples : 100 ; 101 ; 102
   Plage observée : 100 à 169
- Montant_remboursement_virement_bancaire — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Remboursements par virement
   Exemples : 25 ; 0
   Valeurs observées (effectif) : 0 (673) ; 25 (36)
- Montant_paiement_carte_bancaire — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Paiements par carte
   Exemples : 50 ; 0
   Valeurs observées (effectif) : 0 (472) ; 50 (237)
- Montant_paiement_cheque — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Paiements par chèque
   Exemples : 60 ; 0
   Valeurs observées (effectif) : 0 (531) ; 60 (178)
- Montant_remboursement_cheque — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Remboursements par chèque
   Exemples : 10 ; 0
   Valeurs observées (effectif) : 0 (661) ; 10 (48)
- Montant_paiement_espece — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Paiements en espèces
   Exemples : 20 ; 0
   Valeurs observées (effectif) : 0 (567) ; 20 (142)
- Montant_paiement_mandat — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Paiements par mandat
   Exemples : 15 ; 0
   Valeurs observées (effectif) : 0 (620) ; 15 (89)
- Montant_paiement_tpe — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Paiements par TPE
   Exemples : 30 ; 0
   Valeurs observées (effectif) : 0 (590) ; 30 (119)
- Montant_paiement_ecriture_manuelle — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Paiements par écriture manuelle
   Exemples : 12 ; 0
   Valeurs observées (effectif) : 0 (630) ; 12 (79)
- Montant_paiement_moins_remboursement — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 100.
   Description : Paiements nets des remboursements
   Exemples : 450 ; 451 ; 452
   Plage observée : 450 à 549
- Montant_total_accords_reglements_actifs — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Total des accords actifs
   Exemples : 500 ; 0
   Valeurs observées (effectif) : 0 (567) ; 500 (142)
- Indicateur_accords_reglements_actifs — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Accord actif
   Format / valeurs indicatives : Oui / Non
   Exemples : Oui ; Non
   Valeurs observées (effectif) : Non (567) ; Oui (142)
- Montant_echeances_passees_accords_reglements_actifs — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Échéances passées
   Exemples : 150 ; 0
   Valeurs observées (effectif) : 0 (567) ; 150 (142)
- Montant_echeances_passees_respectees_accords_reglements_actifs — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Échéances passées respectées
   Exemples : 100 ; 0
   Valeurs observées (effectif) : 0 (567) ; 100 (142)
- Montant_echeances_passees_non_respectees_accords_reglements_actifs — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Échéances passées non respectées
   Exemples : 50 ; 0
   Valeurs observées (effectif) : 0 (567) ; 50 (142)
- Montant_echeances_en_cours_accords_reglements_actifs — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Échéances en cours
   Exemples : 100 ; 0
   Valeurs observées (effectif) : 0 (567) ; 100 (142)
- Montant_echeances_a_venir_accords_reglements_actifs — Type SQLite : INTEGER. NULL observés : non (0/709). Valeurs distinctes non NULL : 2.
   Description : Échéances à venir
   Exemples : 250 ; 0
   Valeurs observées (effectif) : 0 (567) ; 250 (142)
- Libelle_activite_echeanciers — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 4.
   Description : Activité de l'échéancier
   Format / valeurs indicatives : Début / En cours / Fin / Clos
   Exemples : Début ; En cours ; Fin
   Valeurs observées (effectif) : Début (178) ; Fin (177) ; En cours (177) ; Clos (177)
- Date_actualisation — Type SQLite : TEXT. NULL observés : non (0/709). Valeurs distinctes non NULL : 709.
   Description : Mise à jour
   Exemples : 2025-01-01 12:00:00.000 ; 2025-01-02 12:00:00.000 ; 2025-01-03 12:00:00.000
   Format observé : AAAA-MM-JJ hh:mm:ss.fff
