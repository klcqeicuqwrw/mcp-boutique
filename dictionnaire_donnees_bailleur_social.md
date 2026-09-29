# Dictionnaire de données – schéma DWH

50 tables · 1170 colonnes. Les noms sont préfixés par le schéma (`DWH_Lot` = `DWH.Lot`).

Légende : **PK** clé primaire · **NN** NOT NULL · **RGPD** donnée personnelle.

## Sommaire

- [DWH_AccessionProgramme](#dwh_accessionprogramme) (17 colonnes)
- [DWH_AccessionSuiviContact](#dwh_accessionsuivicontact) (10 colonnes)
- [DWH_AccessionSuiviRéservation](#dwh_accessionsuiviréservation) (8 colonnes)
- [DWH_Affaire](#dwh_affaire) (62 colonnes)
- [DWH_Affaire_pivot](#dwh_affaire_pivot) (4 colonnes)
- [DWH_Bail](#dwh_bail) (21 colonnes)
- [DWH_Calendrier](#dwh_calendrier) (26 colonnes)
- [DWH_Choix_demande_logement](#dwh_choix_demande_logement) (20 colonnes)
- [DWH_Choix_demande_logement2](#dwh_choix_demande_logement2) (23 colonnes)
- [DWH_Client](#dwh_client) (29 colonnes)
- [DWH_Client_historique](#dwh_client_historique) (16 colonnes)
- [DWH_Client_lot_pivot](#dwh_client_lot_pivot) (5 colonnes)
- [DWH_Collaborateur](#dwh_collaborateur) (11 colonnes)
- [DWH_Collaborateur_NEW](#dwh_collaborateur_new) (9 colonnes)
- [DWH_Collaborateur_patrimoine_pivot_NEW](#dwh_collaborateur_patrimoine_pivot_new) (4 colonnes)
- [DWH_Commande](#dwh_commande) (39 colonnes)
- [DWH_Commande_lot_pivot](#dwh_commande_lot_pivot) (3 colonnes)
- [DWH_Commission_attribution_logement](#dwh_commission_attribution_logement) (40 colonnes)
- [DWH_Contentieux_client_historique](#dwh_contentieux_client_historique) (25 colonnes)
- [DWH_Copropriete](#dwh_copropriete) (33 colonnes)
- [DWH_Copropriete_resolution](#dwh_copropriete_resolution) (20 colonnes)
- [DWH_Demande_logement](#dwh_demande_logement) (97 colonnes)
- [DWH_Diagnostic](#dwh_diagnostic) (20 colonnes)
- [DWH_Diagnostic_valeur](#dwh_diagnostic_valeur) (6 colonnes)
- [DWH_Dim_AccessionCommercialisation](#dwh_dim_accessioncommercialisation) (10 colonnes)
- [DWH_Dim_AccessionCommunication](#dwh_dim_accessioncommunication) (7 colonnes)
- [DWH_Dim_AccessionCoutLignage](#dwh_dim_accessioncoutlignage) (8 colonnes)
- [DWH_Dim_AccessionProgrammeDispositif](#dwh_dim_accessionprogrammedispositif) (6 colonnes)
- [DWH_Dim_AccessionSuiviFacturation](#dwh_dim_accessionsuivifacturation) (6 colonnes)
- [DWH_Document_client](#dwh_document_client) (67 colonnes)
- [DWH_Enquete_nouveaux_entrants](#dwh_enquete_nouveaux_entrants) (37 colonnes)
- [DWH_Enquete_satisfaction_envoi](#dwh_enquete_satisfaction_envoi) (10 colonnes)
- [DWH_Equipement](#dwh_equipement) (36 colonnes)
- [DWH_Equipement_OLD](#dwh_equipement_old) (31 colonnes)
- [DWH_Geographie](#dwh_geographie) (13 colonnes)
- [DWH_Geographie_PxM2](#dwh_geographie_pxm2) (6 colonnes)
- [DWH_Intervention](#dwh_intervention) (20 colonnes)
- [DWH_Lot](#dwh_lot) (51 colonnes)
- [DWH_Lot_historique](#dwh_lot_historique) (63 colonnes)
- [DWH_Occupant](#dwh_occupant) (35 colonnes)
- [DWH_Organisation](#dwh_organisation) (10 colonnes)
- [DWH_Organisation_patrimoine_pivot](#dwh_organisation_patrimoine_pivot) (3 colonnes)
- [DWH_Patrimoine](#dwh_patrimoine) (31 colonnes)
- [DWH_Patrimoine_lot_pivot](#dwh_patrimoine_lot_pivot) (4 colonnes)
- [DWH_Piece](#dwh_piece) (12 colonnes)
- [DWH_Proposition_logement](#dwh_proposition_logement) (47 colonnes)
- [DWH_Reglementation](#dwh_reglementation) (7 colonnes)
- [DWH_Releve_compte_client_historique](#dwh_releve_compte_client_historique) (79 colonnes)
- [DWH_Utilisateur](#dwh_utilisateur) (17 colonnes)
- [DWH_Utilisateur_hierarchie](#dwh_utilisateur_hierarchie) (6 colonnes)


### DWH_AccessionProgramme

*Accession · 17 colonnes · PK : `IdAccessionProgramme`*

Programmes d'accession à la propriété, avec leur avancement commercial.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `IdAccessionProgramme` | `int` | PK NN | Identifiant unique de l'accession à la propriété du programme. |
| `NumProjetVente` | `nvarchar(6)` |  | NÂ° projet de vente. |
| `Libelle` | `nvarchar(60)` |  | Libellé en clair d'accession programme. |
| `Code_societe` | `nvarchar(4)` | NN | Code de nomenclature de la société. |
| `Programme` | `nvarchar(4)` |  | Code programme (POT). |
| `Opération` | `nvarchar(4)` |  | Code opération programme. |
| `Tranche` | `nvarchar(4)` |  | Code tranche. |
| `Code_département` | `nvarchar(3)` |  | Code de nomenclature du département. |
| `Code_insee` | `nvarchar(5)` |  | Code de nomenclature INSEE. |
| `Date_os` | `date` |  | Date os. |
| `Date_Lancement_Commercial` | `date` |  | Date lancement com. |
| `Statut` | `nvarchar(30)` |  | Statut d'accession programme. |
| `TypeBien` | `nvarchar(24)` |  | When exists (select * from [STG].[Ikos_PVTESYNDP] U where U.Z1CDTNATUG in  ('LAA') and V.ZZPJID  = U.Z1PJID)… |
| `DispositifVente` | `nvarchar(24)` |  | Prix HT ANRU 7%. |
| `StockInitial` | `int` |  | NOMBRE DE Logements. |
| `StockRestant` | `int` |  | NOMBRE DE Logements. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_AccessionSuiviContact

*Accession · 10 colonnes · PK : `IdAccessionSuiviContact`*

Suivi des contacts commerciaux en accession.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `IdAccessionSuiviContact` | `int` | PK NN | Identifiant unique de l'accession à la propriété suivi du contact. |
| `IdContactAccession` | `int` | NN | Identifiant unique du contact de l'accession à la propriété. |
| `IdProgrammeAccession` | `int` |  | Identifiant unique du programme de l'accession à la propriété. |
| `Nom` | `nvarchar(max)` | RGPD | Nom d'accession suivi contact. |
| `Support_Commercialisation` | `nvarchar(max)` |  | Champ source repris tel quel dans l'entrepôt sous le nom Support_Commercialisation. |
| `Canal_Commercialisation` | `nvarchar(max)` |  | Libellé en clair looker. Looker. |
| `Source_Commercialisation` | `nvarchar(max)` |  | Source Commercialisation : source de la commercialisation. |
| `Campagne_Commercialisation` | `nvarchar(max)` |  | Champ source repris tel quel dans l'entrepôt sous le nom Campagne_Commercialisation. |
| `Date_Contact` | `date` |  | Date du contact. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_AccessionSuiviRéservation

*Accession · 8 colonnes · PK : `IdAccessionSuiviRéservation`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `IdAccessionSuiviRéservation` | `int` | PK NN | Identifiant unique de l'accession à la propriété suivi de la réservation. |
| `IdContactAccession` | `int` | NN | Identifiant unique du contact de l'accession à la propriété. |
| `IdProgrammeAccession` | `int` |  | Identifiant unique du programme de l'accession à la propriété. |
| `Nom` | `nvarchar(max)` | RGPD | Nom d'accession suivi réservation. |
| `Date_Prereservation` | `date` |  | Date prereservation. |
| `Date_Reservation` | `date` |  | Date de la réservation. |
| `Date_Option` | `date` |  | Date option. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Affaire

*Référentiel · 62 colonnes*

Affaires de gestion, maille de regroupement des opérations.

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un) ; `Date_enregistrement` → `DWH.Calendrier.Date` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_affaire` | `nvarchar(50)` |  | Identifiant unique de l'affaire. |
| `ID_client_demandeur_affaire` | `nvarchar(50)` | RGPD | Identifiant unique du client du demandeur de logement de l'affaire. |
| `ID_lot` | `nvarchar(50)` |  | Identifiant unique du lot (unité de gestion IKOS). |
| `ID_patrimoine` | `nvarchar(50)` |  | Identifiant unique du patrimoine. |
| `ID_organisation` | `nvarchar(50)` |  | Identifiant unique de l'organisation. |
| `Code_societe` | `nvarchar(50)` |  | Code de nomenclature de la société. |
| `Code_affaire` | `nvarchar(50)` |  | Code de nomenclature de l'affaire. |
| `Code_client_demandeur_affaire` | `nvarchar(50)` | RGPD | Code de nomenclature du client du demandeur de logement de l'affaire. |
| `Code_mode_contact` | `nvarchar(50)` |  | Code de nomenclature mode du contact. |
| `Libelle_mode_contact` | `nvarchar(50)` |  | Libellé en clair mode du contact. |
| `Code_lot` | `nvarchar(50)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Code_lot_principale_ATR` | `nvarchar(50)` |  | N° UG principale      ATR. |
| `Code_niveau_patrimoine_1` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `Code_niveau_organisation_1` | `nvarchar(50)` |  | Code de nomenclature du niveau de l'organisation de niveau 1. |
| `Code_niveau_organisation_2` | `nvarchar(50)` |  | Code de nomenclature du niveau de l'organisation de niveau 2. |
| `Code_niveau_organisation_3` | `nvarchar(50)` |  | Code de nomenclature du niveau de l'organisation de niveau 3. |
| `Code_nature_processus` | `nvarchar(50)` |  | Code de nomenclature de la nature processus. |
| `Code_processus` | `nvarchar(50)` |  | N° Processus. |
| `Code_categorie_affaire` | `nvarchar(50)` |  | Code de nomenclature de la catégorie de l'affaire. |
| `Libelle_categorie_affaire` | `nvarchar(50)` |  | Libellé en clair de la catégorie de l'affaire. |
| `Code_type_affaire` | `nvarchar(50)` |  | Code de nomenclature du type de l'affaire. |
| `Libelle_type_affaire` | `nvarchar(50)` |  | Libellé en clair du type de l'affaire. |
| `Code_etat_affaire` | `nvarchar(50)` |  | Code de nomenclature de l'état de l'affaire. |
| `Libelle_etat_affaire` | `nvarchar(50)` |  | Libellé en clair de l'état de l'affaire. |
| `Indicateur_statut_etat_affaire` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) du statut de l'état de l'affaire. |
| `Rang_etape` | `nvarchar(50)` |  | Rang étape. |
| `Code_etape` | `nvarchar(50)` |  | Code étape type. |
| `Libelle_etape` | `nvarchar(50)` |  | Libellé étape type. |
| `Code_objet_affaire` | `nvarchar(50)` |  | Code de nomenclature de l'objet de l'affaire. |
| `Libelle_objet_affaire` | `nvarchar(max)` |  | Libellé en clair de l'objet de l'affaire. |
| `Indicateur_validite_objet` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) de validité de l'objet. |
| `Libelle_commentaire` | `nvarchar(max)` |  | Libl com aff 2. |
| `Date_ouverture` | `date` |  | Dates principales. |
| `Date_enregistrement` | `date` |  | Date état enr. |
| `Date_prise_en_charge` | `date` |  | Date état enc. |
| `Date_theorique_prise_en_charge` | `date` |  | Date de calendrier. |
| `Nombre_jour_avant_prise_en_charge` | `int` | RGPD | Code état affaire. |
| `Delai_prise_en_charge` | `int` |  | Date état clos. |
| `Indicateur_retard_prise_en_charge` | `nvarchar(50)` |  | Code catégorie affaire. |
| `Date_commande` | `date` |  | Date de la commande de travaux. |
| `Date_theorique_commande` | `date` |  | Date theorique de la commande de travaux. |
| `Nombre_jour_avant_commande` | `int` | RGPD | Nombre en jours avant de la commande de travaux. |
| `Delai_commande` | `int` |  | Date état enc. |
| `Indicateur_retard_commande` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) retard de la commande de travaux. |
| `Date_cloture` | `date` |  | Date état clos. |
| `Date_theorique_cloture` | `date` |  | Date de calendrier. |
| `Nombre_jour_avant_cloture` | `int` | RGPD | Code catégorie affaire. |
| `Delai_cloture` | `int` |  | Code catégorie affaire. |
| `Indicateur_retard_cloture` | `nvarchar(50)` |  | Code catégorie affaire. |
| `Code_collaborateur_enregistrement` | `nvarchar(50)` |  | Collaborateurs. |
| `Code_collaborateur_suivi` | `nvarchar(50)` |  | Code de nomenclature du collaborateur suivi. |
| `Code_collaborateur_execution` | `nvarchar(50)` |  | Code de nomenclature du collaborateur de l'exécution. |
| `Code_utilisateur_enregistrement` | `nvarchar(50)` |  | Code de nomenclature de l'utilisateur enregistrement. |
| `Code_utilisateur_suivi` | `nvarchar(50)` |  | Code de nomenclature de l'utilisateur suivi. |
| `Code_utilisateur_execution` | `nvarchar(50)` |  | Code de nomenclature de l'utilisateur de l'exécution. |
| `Indicateur_validite_affectation` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) de validité affectation. |
| `Libelle_niveau_reponse` | `nvarchar(50)` |  | Libellé en clair du niveau reponse. |
| `Lien_IKOS_synthese_affaire` | `nvarchar(2048)` |  | Organisme. |
| `Lien_IKOS_liste_affaires_client` | `nvarchar(2048)` | RGPD | Organisme. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Affaire_pivot

*Référentiel · 4 colonnes · PK : `ID_affaire, ID_client_lot`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_affaire` | `nvarchar(10)` | PK NN | Identifiant unique de l'affaire. |
| `ID_client_lot` | `nvarchar(30)` | PK NN RGPD | Identifiant unique du client du lot (unité de gestion IKOS). |
| `Type_pivot` | `nvarchar(10)` | NN | Type pivot. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Bail

*Bail et locataire · 21 colonnes*

Table des baux : contrats de location rattachant un client a un lot, avec leurs dates et conditions.

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un) ; `ID_client` → `DWH.Client.ID_client` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_bail` | `nvarchar(50)` |  | Identifiant unique du bail. |
| `ID_client_lot` | `nvarchar(30)` | RGPD | Identifiant unique du client du lot (unité de gestion IKOS). |
| `ID_client` | `nvarchar(10)` | RGPD | Identifiant unique du client. |
| `ID_lot` | `nvarchar(10)` |  | Identifiant unique du lot (unité de gestion IKOS). |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_client` | `nvarchar(6)` | RGPD | Compte client. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Indicateur_lot_principal` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) du lot (unité de gestion IKOS) principal. |
| `Indicateur_lot_reference_rattachement_patrimoine` | `nvarchar(3)` |  | Définition du lot de référence pour rattachement à la hiérarchie organisation et patrimoine. |
| `Indicateur_occupation_active` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) de l'occupation active. |
| `Date_debut_occupation_lot` | `date` |  | Date de debut de l'occupation du lot (unité de gestion IKOS). |
| `Nombre_jours_depuis_debut_occupation_lot` | `int` | RGPD | Nombre en jours depuis le debut de l'occupation du lot (unité de gestion IKOS). |
| `Nombre_mois_depuis_debut_occupation_lot` | `int` | RGPD | Nombre en mois depuis le debut de l'occupation du lot (unité de gestion IKOS). |
| `Indicateur_nombre_mois_depuis_debut_occupation_lot` | `nvarchar(20)` | RGPD | Indicateur (valeur booléenne ou O/N) du nombre en mois depuis le debut de l'occupation du lot (unité de gesti… |
| `Date_fin_occupation_lot` | `date` |  | Date de fin de l'occupation du lot (unité de gestion IKOS). |
| `Nombre_jours_depuis_fin_occupation_lot` | `int` | RGPD | Nombre en jours depuis le fin de l'occupation du lot (unité de gestion IKOS). |
| `Nombre_mois_depuis_fin_occupation_lot` | `int` | RGPD | Nombre en mois depuis le fin de l'occupation du lot (unité de gestion IKOS). |
| `Indicateur_nombre_mois_depuis_fin_occupation_lot` | `nvarchar(20)` | RGPD | Indicateur (valeur booléenne ou O/N) du nombre en mois depuis le fin de l'occupation du lot (unité de gestion… |
| `Date_reception_preavis` | `date` |  | Date de réception du prévis et délais préavis. |
| `Nombre_jours_delais_prévis` | `int` | RGPD | Délai préavis. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Calendrier

*Référentiel · 26 colonnes · PK : `Date`*

Dimension calendaire de référence, servant d'axe temporel aux analyses.

Jointures : `Annee_mois` → `DWH.Lot_historique.Annee_mois` (plusieurs vers plusieurs) ; `Annee_mois` → `DWH.Releve_compte_client_historique.Annee_mois` (plusieurs vers plusieurs)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `Date` | `date` | PK NN | Date de calendrier. |
| `Annee_mois` | `nvarchar(7)` |  | Annee en mois. |
| `Date_mois_debut` | `date` |  | Date en mois de debut. |
| `Date_mois_fin` | `date` |  | Date en mois de fin. |
| `Annee` | `int` |  | Annee de calendrier. |
| `Date_annee_debut` | `date` |  | Date de l'annee de debut. |
| `Date_annee_fin` | `date` |  | Date de l'annee de fin. |
| `Libelle_Mois` | `nvarchar(20)` |  | Libellé en clair en mois. |
| `Numero_Mois` | `int` |  | Numéro en mois. |
| `Libelle_jour` | `nvarchar(20)` |  | Libellé en clair en jours. |
| `Numero_jour` | `int` |  | Numéro en jours. |
| `Indicateur_jour_ouvre` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) en jours ouvre. |
| `Indicateur_jour_semaine` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) en jours semaine. |
| `Indicateur_jour_ferie` | `nvarchar(3)` |  | Jours fériés fixes. |
| `Semestre` | `nvarchar(20)` |  | Semestre. |
| `Date_semestre_debut` | `date` |  | Date semestre de debut. |
| `Date_semestre_fin` | `date` |  | Date semestre de fin. |
| `Trimestre` | `nvarchar(20)` |  | Trimestre. |
| `Date_trimestre_debut` | `date` |  | Date trimestre de debut. |
| `Date_trimestre_fin` | `date` |  | Date trimestre de fin. |
| `Numero_semaine_annee` | `int` |  | Numéro semaine de l'annee. |
| `Numero_jour_semaine` | `int` |  | Numéro en jours semaine. |
| `Numero_jour_annee` | `int` |  | Numéro en jours de l'annee. |
| `Numero_jour_calendrier` | `int` |  | Numéro en jours du calendrier. |
| `Numero_jour_ouvre_calendrier` | `int` |  | Numéro en jours ouvre du calendrier. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Choix_demande_logement

*Bail et locataire · 20 colonnes*

Choix de localisation exprimes par les demandeurs de logement.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_demande_unique` | `nvarchar(50)` |  | Identifiant unique de la demande de logement unique. |
| `Montant_loyer_logement` | `decimal(10,2)` |  | Montant en euros du loyer du logement. |
| `Montant_loyer_max_recherche` | `decimal(10,2)` |  | Montant en euros du loyer max recherche. |
| `Code_typologie_choix_depart` | `nvarchar(5)` |  | Code de nomenclature typologie choix depart. |
| `Libelle_commune_choix_depart` | `nvarchar(50)` |  | Libellé en clair de la commune choix depart. |
| `Libelle_quartier_choix_depart` | `nvarchar(50)` |  | Libellé en clair du quartier choix depart. |
| `Libelle_commune_quartier_choix_depart` | `nvarchar(100)` |  | Libellé en clair de la commune du quartier choix depart. |
| `Libelle_choix_depart` | `nvarchar(100)` |  | Libellé en clair choix depart. |
| `Code_typologie_choix_arrivee` | `nvarchar(5)` |  | Code de nomenclature typologie choix arrivee. |
| `Libelle_commune_choix_arrivee` | `nvarchar(50)` |  | Libellé en clair de la commune choix arrivee. |
| `Libelle_quartier_choix_arrivee` | `nvarchar(50)` |  | Libellé en clair du quartier choix arrivee. |
| `Libelle_commune_quartier_choix_arrivee` | `nvarchar(100)` |  | Libellé en clair de la commune du quartier choix arrivee. |
| `Libelle_choix_arrivee` | `nvarchar(100)` |  | Libellé en clair choix arrivee. |
| `ID_choix_depart` | `nvarchar(5)` |  | Identifiant unique choix depart. |
| `ID_choix_arrivee` | `nvarchar(5)` |  | Identifiant unique choix arrivee. |
| `ID_echange_unique` | `nvarchar(11)` |  | Identifiant unique échange unique. |
| `Direction` | `nvarchar(15)` |  | Direction. |
| `ID_echange_demande` | `nvarchar(11)` |  | Identifiant unique échange de la demande de logement. |
| `ID_echange_reponse` | `nvarchar(11)` |  | Identifiant unique échange reponse. |
| `Date_actualisation` | `date` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Choix_demande_logement2

*Bail et locataire · 23 colonnes*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_demande_unique_1` | `nvarchar(50)` |  | Identifiant unique de la demande de logement unique de niveau 1. |
| `Montant_loyer_logement_1` | `decimal(10,2)` |  | Montant en euros du loyer du logement de niveau 1. |
| `Montant_loyer_max_recherche_1` | `decimal(10,2)` |  | Montant en euros du loyer max recherche de niveau 1. |
| `Montant_adequation_loyer_1` | `decimal(10,2)` |  | Montant en euros adequation du loyer de niveau 1. |
| `Indicateur_adequation_loyer_1` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) adequation du loyer de niveau 1. |
| `Code_typologie_choix_depart_1` | `nvarchar(50)` |  | Code de nomenclature typologie choix depart de niveau 1. |
| `Libelle_commune_choix_depart_1` | `nvarchar(50)` |  | Libellé en clair de la commune choix depart de niveau 1. |
| `Libelle_quartier_choix_depart_1` | `nvarchar(50)` |  | Libellé en clair du quartier choix depart de niveau 1. |
| `Libelle_commune_quartier_choix_depart_1` | `nvarchar(100)` |  | Libellé en clair de la commune du quartier choix depart de niveau 1. |
| `Libelle_choix_depart_1` | `nvarchar(100)` |  | Libellé en clair choix depart de niveau 1. |
| `ID_echange_demande` | `nvarchar(50)` |  | Identifiant unique échange de la demande de logement. |
| `Code_typologie_choix_depart_2` | `nvarchar(50)` |  | Code de nomenclature typologie choix depart de niveau 2. |
| `Libelle_commune_choix_depart_2` | `nvarchar(50)` |  | Libellé en clair de la commune choix depart de niveau 2. |
| `Libelle_quartier_choix_depart_2` | `nvarchar(50)` |  | Libellé en clair du quartier choix depart de niveau 2. |
| `Libelle_commune_quartier_choix_depart_2` | `nvarchar(100)` |  | Libellé en clair de la commune du quartier choix depart de niveau 2. |
| `Libelle_choix_depart_2` | `nvarchar(100)` |  | Libellé en clair choix depart de niveau 2. |
| `ID_client2` | `nvarchar(10)` | RGPD | N° compte affaire. |
| `ID_demande_unique_2` | `nvarchar(100)` |  | Identifiant unique de la demande de logement unique de niveau 2. |
| `Montant_loyer_logement_2` | `decimal(10,2)` |  | Montant en euros du loyer du logement de niveau 2. |
| `Montant_loyer_max_recherche_2` | `decimal(10,2)` |  | Montant en euros du loyer max recherche de niveau 2. |
| `Montant_adequation_loyer_2` | `decimal(10,2)` |  | Montant en euros adequation du loyer de niveau 2. |
| `Indicateur_adequation_loyer_2` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) adequation du loyer de niveau 2. |
| `Date_actualisation` | `date` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Client

*Bail et locataire · 29 colonnes · PK : `ID_client`*

Dimension des clients : locataires et accédants, avec leurs caracteristiques d'identite et de situation.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client_lot` | `nvarchar(30)` | NN RGPD | Identifiant unique du client du lot (unité de gestion IKOS). |
| `ID_client` | `nvarchar(10)` | PK NN RGPD | Création de l'ID compte client. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_client` | `nvarchar(6)` | RGPD | Compte client. |
| `Nom_prenom_client` | `nvarchar(24)` | RGPD | Nom et prénom client. |
| `Code_type_client` | `nvarchar(3)` | RGPD | Code de nomenclature du type du client. |
| `Libelle_type_client` | `nvarchar(50)` | RGPD | Libellé en clair du type du client. |
| `Code_categorie_menage` | `nvarchar(6)` | RGPD | Code de nomenclature de la catégorie du ménage. |
| `Libelle_composition_familiale` | `nvarchar(24)` |  | Ind type contractant. |
| `Nombre_occupant_enfant` | `float(53)` | RGPD | Nombre de l'occupant du logement enfant. |
| `Nombre_occupant_adulte` | `float(53)` | RGPD | Nombre de l'occupant du logement adulte. |
| `Nombre_occupant_autre` | `float(53)` | RGPD | Nombre de l'occupant du logement autre. |
| `Nombre_occupant_personne` | `float(53)` | RGPD | Nombre de l'occupant du logement personne. |
| `Date_debut_occupation` | `date` |  | Date de premier début d'occupation issu de la CTE ayant permis d'extraire des information de CAUGP. |
| `Date_fin_occupation` | `date` |  | Date de dernière fin d'occupation issu de la CTE ayant permis d'extraire des information de CAUGP. |
| `Indicateur_statut_presence` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) du statut presence. |
| `Annee_revenus_client` | `int` | RGPD | Ajout des revenus issus de la CTE ayant permis de faire la somme des revenus des occupants. |
| `Montant_revenus_client` | `float(53)` | RGPD | Montant en euros revenus du client. |
| `Montant_plafond_plus` | `float(53)` |  | Montant en euros du plafond plus. |
| `Pourcentage_revenus_plafond_plus` | `float(53)` | RGPD | Plafond ressources. |
| `Classe_pourcentage_revenus_plafond_plus` | `nvarchar(24)` | RGPD | Calcul du ratio revenus / plafonds plus. |
| `Code_departement_adresse_temporaire` | `nvarchar(4)` | RGPD | Code de nomenclature du département de l'adresse temporaire. |
| `Code_commune_adresse_temporaire` | `nvarchar(6)` | RGPD | Code de nomenclature de la commune de l'adresse temporaire. |
| `Code_postal_adresse_temporaire` | `nvarchar(6)` | RGPD | Code de nomenclature postal de l'adresse temporaire. |
| `Libelle_commune_adresse_temporaire` | `nvarchar(50)` | RGPD | Libellé en clair de la commune de l'adresse temporaire. |
| `Libelle_numero_rue_adresse_temporaire` | `nvarchar(100)` | RGPD | Libellé en clair numéro de la rue de l'adresse temporaire. |
| `Nom_prenom_CSR_referent` | `nvarchar(255)` | RGPD | CSR référent sur le dossier. |
| `Lien_IKOS_synthese_client` | `nvarchar(2048)` | RGPD | Ajout de l'url vers la synthèse du client IKOS. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Client_historique

*Bail et locataire · 16 colonnes · PK : `ID_client_annee_mois`*

Historisation des clients, permettant le suivi des evolutions de situation dans le temps.

Jointures : `ID_client_annee_mois` → `DWH.Releve_compte_client_historique.ID_client_annee_mois` (un vers un) ; `ID_client` → `DWH.Client.ID_client` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client` | `nvarchar(10)` | RGPD | Insertion des variables. |
| `ID_client_annee_mois` | `nvarchar(20)` | PK NN RGPD | Identifiant unique du client de l'annee en mois. |
| `Annee_mois` | `nvarchar(7)` |  | Annee en mois. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_client` | `nvarchar(6)` | RGPD | Code de nomenclature du client. |
| `Nom_prenom_client` | `nvarchar(24)` | RGPD | Nom prenom du client. |
| `Indicateur_statut_presence` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) du statut presence. |
| `Date_debut_occupation` | `date` |  | Autre condition qui ont été finalement exclues et qui consistait à vérifier si la date de fin avait eu lieu a… |
| `Date_fin_occupation` | `date` |  | Date de fin de l'occupation. |
| `Nombre_jours_depuis_debut_occupation` | `int` | RGPD | Nombre en jours depuis le debut de l'occupation. |
| `Nombre_mois_depuis_debut_occupation` | `int` | RGPD | Nombre en mois depuis le debut de l'occupation. |
| `Indicateur_nombre_mois_depuis_debut_occupation` | `nvarchar(20)` | RGPD | Indicateur (valeur booléenne ou O/N) du nombre en mois depuis le debut de l'occupation. |
| `Nombre_jours_depuis_fin_occupation` | `int` | RGPD | Nombre en jours depuis le fin de l'occupation. |
| `Nombre_mois_depuis_fin_occupation` | `int` | RGPD | Nombre en mois depuis le fin de l'occupation. |
| `Indicateur_nombre_mois_depuis_fin_occupation` | `nvarchar(20)` | RGPD | Indicateur (valeur booléenne ou O/N) du nombre en mois depuis le fin de l'occupation. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Client_lot_pivot

*Patrimoine · 5 colonnes · PK : `ID_client, ID_lot, ID_client_lot`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client_lot` | `nvarchar(30)` | PK NN RGPD | Identifiant unique du client du lot (unité de gestion IKOS). |
| `ID_client` | `nvarchar(10)` | PK NN RGPD | Identifiant unique du client. |
| `ID_lot` | `nvarchar(10)` | PK NN | Identifiant unique du lot (unité de gestion IKOS). |
| `Type_pivot` | `nvarchar(10)` | NN | Type pivot. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Collaborateur

*Organisation · 11 colonnes*

Dimension des collaborateurs du groupe.

Jointures : `ID_organisation` → `DWH.Organisation.ID_organisation` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_organisation` | `nvarchar(20)` |  | Identifiant unique de l'organisation. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_niveau_organisation_1` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 1. |
| `Code_niveau_organisation_2` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 2. |
| `Code_niveau_organisation_3` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 3. |
| `Code_collaborateur` | `nvarchar(10)` |  | Code de nomenclature du collaborateur. |
| `Nom_prenom_collaborateur` | `nvarchar(50)` | RGPD | Nom prenom du collaborateur. |
| `Mail_collaborateur` | `nvarchar(50)` | RGPD | Adresse mail user. |
| `Code_fonction` | `nvarchar(4)` |  | Code fonct. |
| `Libelle_fonction` | `nvarchar(50)` |  | Libl fonct. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Collaborateur_NEW

*Organisation · 9 colonnes*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_collaborateur_fonction` | `nvarchar(30)` |  | Identifiant unique du collaborateur fonction. |
| `ID_collaborateur` | `nvarchar(20)` |  | Identifiant unique du collaborateur. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_collaborateur` | `nvarchar(10)` |  | Code de nomenclature du collaborateur. |
| `Nom_prenom_collaborateur` | `nvarchar(50)` | RGPD | Nom prenom du collaborateur. |
| `Mail_collaborateur` | `nvarchar(50)` | RGPD | Mail collaborateur : adresse de courriel du collaborateur. |
| `Code_fonction` | `nvarchar(4)` |  | Code de nomenclature fonction. |
| `Libelle_fonction` | `nvarchar(50)` |  | Libellé en clair fonction. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Collaborateur_patrimoine_pivot_NEW

*Patrimoine · 4 colonnes · PK : `ID_collaborateur_fonction, ID_patrimoine`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_collaborateur_fonction` | `varchar(30)` | PK NN | Identifiant unique du collaborateur fonction. |
| `ID_collaborateur` | `varchar(20)` | NN | Identifiant unique du collaborateur. |
| `ID_patrimoine` | `varchar(20)` | PK NN | Identifiant unique du patrimoine. |
| `Date_actualisation` | `datetime` | NN | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Commande

*Technique et maintenance · 39 colonnes · PK : `ID_commande`*

Commandes de travaux passees auprès des fournisseurs.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_commande` | `varchar(15)` | PK NN | Identifiant unique de commande : concatène le code société et le numéro de commande. |
| `Code_societe` | `varchar(3)` |  | Code de nomenclature de la société. |
| `Numero_commande` | `varchar(6)` |  | Numéro de la commande. |
| `ID_organisation` | `varchar(15)` |  | Identifiant unique de l'organisation. |
| `Code_niveau_organisation_1` | `varchar(4)` |  | Code_organisation_niveau_1. |
| `Code_niveau_organisation_2` | `varchar(4)` |  | Code_organisation_niveau_2. |
| `Code_niveau_organisation_3` | `varchar(4)` |  | Code_organisation_niveau_3. |
| `Code_niveau_patrimoine_1` | `varchar(4)` |  | Code de la résidence (HP1). |
| `Code_niveau_patrimoine_2` | `varchar(4)` |  | Code du batîment (HP2). |
| `Code_niveau_patrimoine_3` | `varchar(4)` |  | Code de la cage d'escalier (HP3). |
| `Code_lot` | `varchar(6)` |  | Code du lot. |
| `Type_commande` | `varchar(6)` |  | Type de commande. |
| `Libelle_type_commande` | `varchar(255)` |  | Libellé type de commande. |
| `Libelle_objet_commande_1` | `varchar(500)` |  | Objet 1 de la commande. |
| `Libelle_objet_commande_2` | `varchar(500)` |  | Objet 2 de la commande. |
| `Commentaire_commande` | `varchar(1000)` |  | Commentaire de la commande. |
| `Montant_HT` | `decimal(15,2)` |  | Montant en euros hors taxes. |
| `Montant_TVA` | `decimal(15,2)` |  | Montant en euros de la TVA. |
| `Montant_TTC` | `decimal(15,2)` |  | Montant en euros toutes taxes comprises. |
| `Code_tiers` | `varchar(15)` |  | Code du tiers. |
| `Libelle_tiers` | `varchar(100)` |  | Libellé du tiers. |
| `Telephone_fixe_tiers` | `varchar(20)` | RGPD | Téléphone fixe du tiers. |
| `Telephone_portable_tiers` | `varchar(20)` | RGPD | Téléphone portable du tiers. |
| `Mail_tiers` | `varchar(100)` | RGPD | Adresse mail du tiers. |
| `Code_collaborateur_executant_commande` | `varchar(6)` |  | Code de l'utilisateur passant la commande. |
| `Code_utilisateur_executant_commande` | `varchar(30)` |  | Code de l'utilisateur passant la commande. |
| `Date_enregistrement_commande` | `datetime` |  | Jalons de la commande (formatées en DATE à partir d'un format AAAAMMJJ). |
| `Date_signature_commande` | `datetime` |  | Date signature de la commande de travaux. |
| `Date_debut_execution_commande` | `datetime` |  | Date de debut de l'exécution de la commande de travaux. |
| `Date_fin_execution_commande` | `datetime` |  | Date de fin de l'exécution de la commande de travaux. |
| `Nombre_jours_depuis_commande` | `varchar(6)` | RGPD | Nombre de jour depuis la commande. |
| `Indicateur_categorie_delai_commande` | `varchar(30)` |  | Indicateur (valeur booléenne ou O/N) de la catégorie delai de la commande de travaux. |
| `Taux_execution_commande` | `decimal(5,2)` |  | Taux d'éxécution de la commande. |
| `Libelle_etat_commande` | `varchar(40)` |  | Libellé état de la commande. |
| `Indicateur_charge_a_payer` | `varchar(5)` |  | N° de commande. |
| `Statut_commande` | `varchar(6)` |  | Statut de la commande. |
| `Libelle_statut_commande` | `varchar(30)` |  | Libellé statut de la commande. |
| `Lien_IKOS_commande` | `varchar(1000)` |  | Lien URL vers la synthèse de Diagnostic. |
| `Date_actualisation` | `datetime` |  | Date d'actualisation des données. |


### DWH_Commande_lot_pivot

*Patrimoine · 3 colonnes · PK : `ID_commande, ID_lot`*

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un) ; `ID_commande` → `DWH.Commande.ID_commande` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_commande` | `varchar(15)` | PK NN | Identifiant unique de la commande de travaux. |
| `ID_lot` | `varchar(10)` | PK NN | Identifiant unique du lot (unité de gestion IKOS). |
| `Date_actualisation` | `datetime` | NN | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Commission_attribution_logement

*Bail et locataire · 40 colonnes*

Passages en commission d'attribution des logements (CALS) et decisions rendues.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_demande_unique` | `nvarchar(24)` |  | Identifiant unique de la demande de logement unique. |
| `ID_bailleur` | `nvarchar(13)` |  | Identifiant unique bailleur. |
| `Code_niveau_patrimoine_1` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `ID_CAL` | `nvarchar(10)` |  | Identifiant unique commission d'attribution. |
| `Date_inscription_commission` | `date` |  | Date inscription de la commission d'attribution (CALS). |
| `Date_seance_commission` | `date` |  | Date seance de la commission d'attribution (CALS). |
| `Libelle_motif_attribution` | `nvarchar(100)` | RGPD | Libellé en clair du motif de l'attribution. |
| `Date_limite_condition_suspensive` | `date` |  | Date limite condition suspensive. |
| `Code_rang` | `nvarchar(2)` |  | Code de nomenclature du rang. |
| `Code_agence` | `nvarchar(4)` | RGPD | Code de nomenclature de l'agence. |
| `Libelle_agence` | `nvarchar(70)` | RGPD | Libellé en clair de l'agence. |
| `Utilisateur_inscription` | `nvarchar(70)` |  | Utilisateur inscription. |
| `Libelle_motif_rejet` | `nvarchar(100)` |  | Libellé en clair du motif rejet. |
| `Taux_effort` | `decimal(10,2)` |  | Taux ou pourcentage effort. |
| `Montant_APL` | `decimal(10,2)` |  | Montant en euros de l'APL (aide personnalisee au logement). |
| `Montant_reste_a_vivre` | `decimal(10,2)` |  | Montant en euros reste à vivre. |
| `Montant_autres_charges` | `decimal(10,2)` |  | Montant en euros autrès des charges locatives. |
| `Libelle_motif_non_attribution` | `nvarchar(100)` | RGPD | Libellé en clair du motif non de l'attribution. |
| `Montant_mensualité` | `decimal(10,2)` |  | Montant en euros mensualité. |
| `Montant_residuel` | `decimal(10,2)` |  | Montant en euros residuel. |
| `Libelle_decision` | `nvarchar(24)` |  | Libellé en clair decision. |
| `Montant_revenu_unité_consommation` | `decimal(10,2)` | RGPD | Montant en euros revenu unité consommation. |
| `Indicateur_premier_quartile` | `nvarchar(4)` |  | Indicateur (valeur booléenne ou O/N) premier quartile. |
| `Montant_RLS` | `decimal(10,2)` |  | Montant en euros rls. |
| `Libelle_reservataire_proposition` | `nvarchar(70)` |  | Libellé en clair réservataire de la proposition de logement. |
| `ID_prospection_imhoweb` | `nvarchar(24)` |  | Identifiant unique prospection imhoweb. |
| `Annee_RFR` | `nvarchar(4)` |  | Annee rfr. |
| `Montant_RFR` | `decimal(10,2)` |  | Montant en euros rfr. |
| `Montant_plafond` | `decimal(10,2)` |  | Montant en euros du plafond. |
| `Taux_plafond` | `decimal(10,2)` |  | Taux ou pourcentage du plafond. |
| `Indicateur_logement_flux` | `nvarchar(4)` |  | Indicateur (valeur booléenne ou O/N) du logement flux. |
| `Libelle_motif_hors_flux` | `nvarchar(50)` |  | Libellé en clair du motif hors flux. |
| `Libelle_delagataire_commission` | `nvarchar(70)` |  | Libellé en clair delagataire de la commission d'attribution (CALS). |
| `ID_designataire_commission` | `nvarchar(10)` |  | Identifiant unique designataire de la commission d'attribution (CALS). |
| `ID_delegataire_commission` | `nvarchar(70)` |  | Identifiant unique délégataire de la commission d'attribution (CALS). |
| `Libelle_decision_autre` | `nvarchar(24)` |  | Libellé en clair decision autre. |
| `Code_rang_autre` | `nvarchar(3)` |  | Code de nomenclature du rang autre. |
| `Libelle_motif_decision_autre` | `nvarchar(100)` |  | Libellé en clair du motif decision autre. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Contentieux_client_historique

*Bail et locataire · 25 colonnes*

Historisation des situations de contentieux et d'impayé des clients.

Jointures : `ID_client_annee_mois` → `DWH.Client_historique.ID_client_annee_mois` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client` | `nvarchar(10)` | RGPD | Identifiant unique du client. |
| `ID_client_annee_mois` | `nvarchar(20)` | NN RGPD | Identifiant unique du client de l'annee en mois. |
| `Annee_mois` | `nvarchar(7)` |  | Annee en mois. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_client` | `nvarchar(6)` | RGPD | Code de nomenclature du client. |
| `Libelle_procedure` | `nvarchar(24)` |  | Libellé en clair de la procédure stockée. |
| `Libelle_etape_procedure` | `nvarchar(255)` |  | Libellé en clair etape de la procédure stockée. |
| `Date_debut_procedure` | `date` |  | Date de debut de la procédure stockée. |
| `Date_fin_procedure` | `date` |  | Date de fin de la procédure stockée. |
| `Libelle_procedure_cumulable` | `nvarchar(24)` |  | Libellé en clair de la procédure stockée cumulable. |
| `Indicateur_dossier_titre` | `nvarchar(10)` |  | Date début occupation. |
| `Date_prescription` | `date` |  | Date début occupation. |
| `Nombre_jour_delai_prescription` | `int` | RGPD | Date début occupation. |
| `Classe_nombre_jour_delai_prescription` | `nvarchar(20)` | RGPD | Date début occupation. |
| `Indicateur_depassement_delais_prescription` | `nvarchar(10)` |  | Date début occupation. |
| `Indicateur_procedure_surendettement_active` | `nvarchar(10)` |  | Code procédure. |
| `Indicateur_procedure_enquete_active` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) de la procédure stockée de l'enquete active. |
| `Indicateur_procedure_saisie_active` | `nvarchar(10)` |  | Code procédure. |
| `Indicateur_procedure_plan_active` | `nvarchar(10)` |  | Code procédure. |
| `Indicateur_procedure_capex_active` | `nvarchar(10)` |  | Code procédure. |
| `Indicateur_plan_PRP` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) plan prp. |
| `Raison_sociale_huissier_referent` | `nvarchar(255)` |  | Nom/raison sociale. |
| `Indicateur_check_mois_en_cours` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) check en mois en cours. |
| `Indicateur_check_sortie` | `nvarchar(150)` |  | Indicateur (valeur booléenne ou O/N) check de sortie des lieux. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Copropriete

*Accession · 33 colonnes*

Copropriétés dans lesquelles le groupe detient des lots.

Jointures : `ID_patrimoine` → `DWH.Patrimoine.ID_patrimoine` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_copropriete` | `nvarchar(50)` |  | Identifiant unique de la copropriété. |
| `ID_copropriete_document_source` | `nvarchar(100)` |  | Identifiant unique de la copropriété du document de la source. |
| `ID_patrimoine` | `nvarchar(20)` |  | Identifiant unique du patrimoine. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_niveau_patrimoine_1` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `Date_document_source` | `date` |  | Date du document de la source. |
| `Type_document_source` | `nvarchar(3)` | NN | Type du document de la source. |
| `Type_copropriete` | `nvarchar(5)` |  | Type de la copropriété. |
| `ID_immatriculation_copropriete` | `nvarchar(50)` |  | Identifiant unique immatriculation de la copropriété. |
| `Nom_copropriete` | `nvarchar(255)` | RGPD | Nom de la copropriété. |
| `Date_immatriculation_copropriete` | `date` |  | > Date d'immatriculation de la copropriété. |
| `Date_reglement_copropriete` | `date` |  | > Date d'immatriculation de la copropriété. |
| `Adresse_complete_copropriete` | `nvarchar(500)` | RGPD | Adresse complète de la copropriété. |
| `Adresse_copropriete` | `nvarchar(255)` | RGPD | Adresse de la copropriété. |
| `Code_postal_copropriete` | `nvarchar(5)` |  | Code de nomenclature postal de la copropriété. |
| `Libelle_commune_copropriete` | `nvarchar(255)` |  | Libellé en clair de la commune de la copropriété. |
| `ID_syndic` | `nvarchar(24)` |  | Identifiant unique du syndic. |
| `Nom_syndic` | `nvarchar(255)` | RGPD | Nom du syndic. |
| `Adresse_complete_syndic` | `nvarchar(500)` | RGPD | Adresse complète du syndic. |
| `Adresse_syndic` | `nvarchar(128)` | RGPD | Adresse du syndic. |
| `Code_postal_syndic` | `nvarchar(5)` |  | Code de nomenclature postal du syndic. |
| `Libelle_commune_syndic` | `nvarchar(255)` |  | Libellé en clair de la commune du syndic. |
| `Tel_syndic` | `nvarchar(15)` | RGPD | Coordonnées syndic : On récupère ici les coordonnées depuis la table IKOS des tiers. |
| `Mail_syndic` | `nvarchar(64)` | RGPD | Adresse e-mail tiers. |
| `Etat_mandat_copropriete` | `nvarchar(100)` |  | > État du mandat en cours (RNIC). |
| `Date_fin_mandat_copropriete` | `date` |  | > Date de fin de mandat (RNIC). |
| `Tantiemes_aiguillon` | `decimal(20,2)` |  | Statut. |
| `Total_tantiemes_copropriete` | `decimal(20,2)` |  | Total des tantiemes de copropriété de la copropriété. |
| `Date_integration` | `datetime` |  | Date de l'intégration. |
| `Date_validation` | `datetime` |  | Date validation. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Copropriete_resolution

*Accession · 20 colonnes*

Résolutions votées en assemblée générale de copropriété.

Jointures : `ID_copropriete` → `DWH.Copropriete.ID_copropriete` (plusieurs vers un) ; `Date_document_source` → `DWH.Calendrier.Date` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_copropriete` | `nvarchar(50)` |  | Identifiant unique de la copropriété. |
| `ID_copropriete_document_source` | `nvarchar(100)` |  | Identifiant unique de la copropriété du document de la source. |
| `ID_patrimoine` | `nvarchar(20)` |  | Identifiant unique du patrimoine. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_niveau_patrimoine_1` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(50)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `Date_document_source` | `date` |  | Date du document de la source. |
| `Type_document_source` | `nvarchar(20)` | NN | Type du document de la source. |
| `Type_copropriete` | `nvarchar(5)` |  | Type de la copropriété. |
| `Numero_resolution_brut` | `nvarchar(8)` | NN | Numéro de la résolution d'assemblée générale brut. |
| `Numero_resolution_tri` | `decimal(8,2)` |  | Dans ta procédure, lors de l'insertion. |
| `Indicateur_approbation_resolution` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) approbation de la résolution d'assemblée générale. |
| `Description_resolution` | `nvarchar(500)` |  | Description résolution : cription de la résolution d'assemblée générale. |
| `Classification_resolution` | `nvarchar(30)` |  | > Classification des résolution par grande famille (Travaux, JURIDIQUE, VIE, ..). |
| `Montant_engage_resolution` | `decimal(20,2)` | RGPD | Montant en euros engage de la résolution d'assemblée générale. |
| `Indicateur_dernier_document` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) dernier du document. |
| `Lien_URL_GED` | `nvarchar(500)` |  | > Lien_URL_document_source  -- ← NOUVELLE LIGNE. |
| `Date_integration` | `datetime` |  | Date de l'intégration. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Demande_logement

*Bail et locataire · 97 colonnes*

Demandes de logement social issues du portail IMHOWEB, avec leur statut d'instruction.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client` | `nvarchar(10)` | RGPD | Identifiant unique du client. |
| `Code_client` | `nvarchar(6)` | RGPD | Code de nomenclature du client. |
| `Libelle_present_parti` | `nvarchar(24)` |  | Date début occupation. |
| `Indicateur_rapprochement_demande_client` | `nvarchar(5)` | RGPD | Ajout d'un indicateur de réussite du rapprochement demande imhoweb - client AC. |
| `Code_titre_demandeur` | `nvarchar(13)` | RGPD | Code de nomenclature titre du demandeur de logement. |
| `Libelle_titre_demandeur` | `nvarchar(50)` | RGPD | Libellé en clair titre du demandeur de logement. |
| `Nom_demandeur` | `nvarchar(50)` | RGPD | Nom du demandeur de logement. |
| `Prenom_demandeur` | `nvarchar(50)` | RGPD | Prenom du demandeur de logement. |
| `Date_naissance_demandeur` | `date` | RGPD | Date naissance du demandeur de logement. |
| `Libelle_statut_demandeur` | `nvarchar(50)` | RGPD | Libellé en clair du statut du demandeur de logement. |
| `ID_demande_imhoweb` | `nvarchar(24)` |  | Identifiant unique de la demande de logement imhoweb. |
| `ID_demande_unique` | `nvarchar(50)` |  | Identifiant unique de la demande de logement unique. |
| `Code_departement` | `nvarchar(3)` |  | Code de nomenclature du département. |
| `Date_depot` | `date` |  | Date du dépôt de garantie. |
| `Date_creation` | `date` |  | Date de création. |
| `Date_validation` | `date` |  | Date validation. |
| `Date_renouvellement` | `date` |  | Date renouvellement. |
| `Date_passage_delai_anormalement_long` | `date` | RGPD | Date passage delai anormalement long. |
| `Indicateur_delai_anormalement_long` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) delai anormalement long. |
| `Libelle_categorie_menage` | `nvarchar(50)` | RGPD | Libellé en clair de la catégorie du ménage. |
| `Libelle_etat_demande` | `nvarchar(24)` |  | Libellé en clair de l'état de la demande de logement. |
| `Libelle_organisme_saisie` | `nvarchar(50)` |  | Libellé en clair organisme saisie. |
| `Code_postal` | `nvarchar(5)` |  | Code de nomenclature postal. |
| `Libelle_commune` | `nvarchar(50)` |  | Libellé en clair de la commune. |
| `Code_INSEE_commune` | `nvarchar(5)` |  | Code de nomenclature INSEE de la commune. |
| `Adresse` | `nvarchar(50)` | RGPD | Adresse de demande logement. |
| `Code_quartier` | `nvarchar(5)` |  | Code de nomenclature du quartier. |
| `Libelle_quartier` | `nvarchar(50)` |  | Libellé en clair du quartier. |
| `Nombre_enfants` | `int` | RGPD | Nombre enfants. |
| `Nombre_enfants_a_charge` | `int` | RGPD | Nombre enfants a charge. |
| `Nombre_enfants_droit_de_visite` | `int` | RGPD | Nombre enfants droit de visite. |
| `Nombre_enfants_garde_alternee` | `int` | RGPD | Nombre enfants garde alternee. |
| `Nombre_autres_personnes` | `int` | RGPD | Nombre autrès personnes. |
| `Nombre_total_occupants` | `int` | RGPD | Nombre total occupants. |
| `Nombre_enfants_attendus` | `int` | RGPD | Nombre enfants attendus. |
| `Date_naissance_prevue` | `date` | RGPD | Date naissance prévue. |
| `Nombre_personnes_handicapees` | `int` | RGPD | Nombre personnes handicapees. |
| `Code_categorie_menage` | `nvarchar(2)` | RGPD | Code de nomenclature de la catégorie du ménage. |
| `Quotient_familial` | `decimal(10,2)` |  | Champ source repris tel quel dans l'entrepôt sous le nom Quotient_familial. |
| `Ressources_par_unite_consommation` | `decimal(10,2)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom Ressources_par_unite_consommation. |
| `Code_statut_occupation` | `nvarchar(5)` |  | Code de nomenclature du statut de l'occupation. |
| `Libelle_statut_occupation` | `nvarchar(100)` |  | Libellé en clair du statut de l'occupation. |
| `Date_statut_occupation` | `date` |  | Date du statut de l'occupation. |
| `ID_bailleur` | `nvarchar(13)` |  | Identifiant unique bailleur. |
| `Libelle_bailleur` | `nvarchar(50)` |  | Libellé en clair bailleur. |
| `Montant_APL_logement` | `decimal(10,2)` |  | Montant en euros de l'APL (aide personnalisee au logement) du logement. |
| `Montant_loyer_logement` | `decimal(10,2)` |  | Montant en euros du loyer du logement. |
| `Code_type_lot_logement` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) du logement. |
| `Libelle_individuel_collectif` | `nvarchar(13)` |  | Libellé en clair individuel collectif. |
| `Surface_habitable` | `decimal(10,2)` |  | Surface en metrès carrés habitable. |
| `Nombre_personnes` | `int` | RGPD | Nombre personnes. |
| `Indicateur_mutation` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) de la mutation. |
| `Type_mutation` | `nvarchar(13)` |  | Qualification du type de mutation Interne/Externe. |
| `Mois_ressources` | `nvarchar(2)` | RGPD | Mois ressources. |
| `Annee_ressources` | `nvarchar(4)` | RGPD | Annee ressources. |
| `Montant_ressources` | `decimal(10,2)` | RGPD | Montant en euros ressources. |
| `Annee_reference_N` | `nvarchar(4)` |  | Annee de référence n. |
| `Annee_reference_N-1` | `nvarchar(4)` |  | Annee de référence n-1. |
| `Annee_reference_N-2` | `nvarchar(4)` |  | Annee de référence n-2. |
| `Annee_reference_N+1` | `nvarchar(4)` |  | Annee de référence n+1. |
| `Montant_reference` | `decimal(10,2)` |  | Montant en euros de référence. |
| `Montant_reference_N-1` | `decimal(10,2)` |  | Montant en euros de référence n-1. |
| `Montant_referenceN-2` | `decimal(10,2)` |  | Montant en euros de référence n-2. |
| `Montant_reference_N+1` | `decimal(10,2)` |  | Montant en euros de référence n+1. |
| `Plafond_ressource_N` | `decimal(10,4)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom Plafond_ressource_N. |
| `Plafond_ressource_N-1` | `decimal(10,4)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom Plafond_ressource_N-1. |
| `Plafond_ressource_N-2` | `decimal(10,4)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom Plafond_ressource_N-2. |
| `Plafond_ressource_N+1` | `decimal(10,4)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom Plafond_ressource_N+1. |
| `Libelle_individuel_collectif_recherche` | `nvarchar(13)` |  | Libellé en clair individuel collectif recherche. |
| `Code_type_lot_recherche_1` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) recherche de niveau 1. |
| `Code_type_lot_recherche_2` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) recherche de niveau 2. |
| `Code_type_lot_recherche_3` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) recherche de niveau 3. |
| `Code_type_lot_recherche_4` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) recherche de niveau 4. |
| `Code_type_lot_recherche_5` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) recherche de niveau 5. |
| `Code_type_lot_recherche_6` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) recherche de niveau 6. |
| `Code_type_lot_recherche_7` | `nvarchar(5)` |  | Code de nomenclature du type du lot (unité de gestion IKOS) recherche de niveau 7. |
| `Indicateur_parking_recherche` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) parking recherche. |
| `Indicateur_rez_de_chaussee_recherche` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) rez de chaussee recherche. |
| `Indicateur_sans_assenceur_recherche` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) sans assenceur recherche. |
| `Indicateur_adapte_handicap_recherche` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) adapté handicap recherche. |
| `Loyer_max_recherche` | `decimal(10,2)` |  | Champ source repris tel quel dans l'entrepôt sous le nom Montant_loyer_max_recherche. |
| `Indicateur_demande_elargie_recherche` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) de la demande de logement elargie recherche. |
| `Code_motif_demande_1` | `nvarchar(5)` |  | Code de nomenclature du motif de la demande de logement de niveau 1. |
| `Libelle_motif_demande_1` | `nvarchar(70)` |  | Libellé en clair du motif de la demande de logement de niveau 1. |
| `Code_motif_demande_2` | `nvarchar(5)` |  | Code de nomenclature du motif de la demande de logement de niveau 2. |
| `Libelle_motif_demande_2` | `nvarchar(70)` |  | Libellé en clair du motif de la demande de logement de niveau 2. |
| `Code_motif_demande_3` | `nvarchar(5)` |  | Code de nomenclature du motif de la demande de logement de niveau 3. |
| `Libelle_motif_demande_3` | `nvarchar(70)` |  | Libellé en clair du motif de la demande de logement de niveau 3. |
| `Indicateur_demande_handicap` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) de la demande de logement handicap. |
| `Indicateur_QPV` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) du quartier prioritaire (QPV). |
| `Libelle_QPV` | `nvarchar(70)` |  | Libellé en clair du quartier prioritaire (QPV). |
| `Nombre_unite_consommation` | `decimal(10,2)` | RGPD | Nombre unité consommation. |
| `Code_client_imhoweb` | `nvarchar(50)` | RGPD | Code de nomenclature du client imhoweb. |
| `Indicateur_demande_prioritaire` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) de la demande de logement prioritaire. |
| `Libelle_motif_priorite` | `nvarchar(100)` |  | Libellé en clair du motif priorite. |
| `Indicateur_demande_confort` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) de la demande de logement confort. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Diagnostic

*Patrimoine · 20 colonnes · PK : `ID_diagnostic`*

Diagnostics techniques et réglementaires réalisés sur le patrimoine (DPE, amiante, plomb, etc.).

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un) ; `Date_debut_diagnostic` → `DWH.Calendrier.Date` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_diagnostic` | `varchar(15)` | PK NN | Clé unique diagnostic. |
| `ID_lot` | `varchar(15)` |  | Clé lot. |
| `Code_societe` | `varchar(3)` |  | Identifiants et codes. |
| `Code_lot` | `varchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Numero_diagnostic` | `varchar(10)` |  | Numéro du diagnostic technique. |
| `Numero_dossier` | `varchar(10)` |  | N° dossier technique. |
| `Nature_diagnostic` | `varchar(10)` |  | Arborescence diagnostics. |
| `Type_diagnostic` | `varchar(10)` |  | Type du diagnostic technique. |
| `Code_diagnostic` | `varchar(15)` |  | Code de nomenclature du diagnostic technique. |
| `Libelle_diagnostic` | `varchar(255)` |  | Libellé en clair du diagnostic technique. |
| `Date_injection_diagnostic` | `date` |  | Dates liées aux flux de gestion des diagnostics. |
| `Date_debut_diagnostic` | `date` |  | Dates au format YYYYMMDD (DECIMAL). |
| `Date_fin_diagnostic` | `date` |  | Date de fin du diagnostic technique. |
| `Indicateur_diagnostic_le_plus_recent` | `nvarchar(5)` |  | Flag diagnostic le plus récent (par lot et libellé). |
| `Indicateur_diagnostic_perime` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) du diagnostic technique perime. |
| `Nombre_jours_avant_peremption` | `int` | RGPD | Nombre de jours avant péremption. |
| `Lien_URL_diagnostic` | `nvarchar(500)` |  | Lien URL vers la synthèse de Diagnostic. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |
| `Famille_diagnostic` | `varchar(30)` |  | Famille diagnostic : famille du diagnostic technique. |
| `Lien_IKOS_GED_diagnostic` | `nvarchar(500)` |  | Lien GED unique. |


### DWH_Diagnostic_valeur

*Patrimoine · 6 colonnes · PK : `ID_diagnostic, Type_valeur`*

Valeurs détaillées relevees pour chaque diagnostic.

Jointures : `ID_diagnostic` → `DWH.Diagnostic.ID_diagnostic` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_diagnostic` | `varchar(15)` | PK NN | Identifiant unique du diagnostic technique. |
| `Code_societe` | `varchar(3)` |  | Code de nomenclature de la société. |
| `Numero_diagnostic` | `varchar(10)` |  | Numéro du diagnostic technique. |
| `Type_valeur` | `varchar(30)` | PK NN | Type de la valeur. |
| `Valeur` | `varchar(10)` |  | Valeur de diagnostic valeur. |
| `Unite` | `varchar(10)` |  | Unité de mesure de diagnostic valeur. |


### DWH_Dim_AccessionCommercialisation

*Accession · 10 colonnes · PK : `IdDim_AccessionCommercialisation`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `IdDim_AccessionCommercialisation` | `int` | PK NN | Identifiant unique dim de l'accession à la propriété de la commercialisation. |
| `IdProgrammeAccession` | `int` | NN | Identifiant unique du programme de l'accession à la propriété. |
| `Mois_Commercialisation` | `date` |  | Mois de la commercialisation. |
| `Origine_Commercilisation` | `nvarchar(max)` |  | Origine Commercilisation. |
| `Source_Commercialisation` | `nvarchar(max)` |  | Source Commercialisation : source de la commercialisation. |
| `Nombre_Contacts` | `int` | RGPD | Nombre contacts. |
| `Nombre_Reservation` | `int` | RGPD | Nombre de la réservation. |
| `Nombre_Option` | `int` | RGPD | Nombre option. |
| `Nombre_PreReservation` | `int` | RGPD | Nombre pre de la réservation. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Dim_AccessionCommunication

*Accession · 7 colonnes · PK : `IdDim_AccessionCommunication`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `IdDim_AccessionCommunication` | `int` | PK NN | Identifiant unique dim de l'accession à la propriété communication. |
| `IdProgrammeAccession` | `int` | NN | Identifiant unique du programme de l'accession à la propriété. |
| `Date_communication` | `date` |  | Date communication. |
| `Libellé_action` | `nvarchar(max)` |  | Libellé en clair action. |
| `Détail_action` | `nvarchar(max)` |  | Champ source repris tel quel dans l'entrepôt sous le nom Détail_action. |
| `Cout_action` | `decimal(15,2)` |  | Coût action. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Dim_AccessionCoutLignage

*Accession · 8 colonnes · PK : `IdDim_AccessionCoutLignage`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `IdDim_AccessionCoutLignage` | `int` | PK NN RGPD | Identifiant unique dim de l'accession à la propriété coût lignage. |
| `IdProgrammeAccession` | `int` | NN | Identifiant unique du programme de l'accession à la propriété. |
| `dim__portail` | `nvarchar(max)` |  | Libellé en clair looker. Looker. |
| `dim__mois` | `nvarchar(max)` |  | Champ source repris tel quel dans l'entrepôt sous le nom dim__mois. |
| `stat__pv_unitaire` | `nvarchar(max)` |  | Champ source repris tel quel dans l'entrepôt sous le nom stat__pv_unitaire. |
| `stat__nombre_leads_factures` | `nvarchar(max)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom stat__nombre_leads_factures. |
| `stat__pv_total` | `nvarchar(max)` |  | Stat pv total : statut pv total. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Dim_AccessionProgrammeDispositif

*Accession · 6 colonnes · PK : `IdDim_AccessionProgrammeDispositif`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `IdDim_AccessionProgrammeDispositif` | `int` | PK NN | Identifiant unique dim de l'accession à la propriété du programme du dispositif de vente. |
| `IdProgrammeAccession` | `int` | NN | Identifiant unique du programme de l'accession à la propriété. |
| `Dispositif` | `nvarchar(10)` |  | Dispositif : dispositif de vente. |
| `StockInitial` | `int` |  | Stock Initial. |
| `StockRestant` | `int` |  | Statut dossier. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Dim_AccessionSuiviFacturation

*Quittancement et comptabilité · 6 colonnes · PK : `Id_AccessionSuiviFacturation`*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `Id_AccessionSuiviFacturation` | `int` | PK NN | Identifiant unique de l'accession à la propriété suivi facturation. |
| `IdProgrammeAccession` | `int` | NN | Identifiant unique du programme de l'accession à la propriété. |
| `Budget_Alloue` | `decimal(15,2)` |  | Budget Alloue. |
| `Montant_Facture` | `decimal(15,2)` |  | Montant en euros de la facture. |
| `Solde` | `decimal(15,2)` |  | Montant en euros de la facture. Facturé. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Document_client

*Bail et locataire · 67 colonnes*

Documents rattaches au dossier d'un client.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `Code_organisme` | `nvarchar(10)` |  | Organisme. |
| `ID_lot` | `nvarchar(10)` |  | Identifiant unique du lot (unité de gestion IKOS). |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `ID_client` | `nvarchar(10)` | RGPD | Identifiant unique du client. |
| `Code client` | `nvarchar(6)` | RGPD | Code de nomenclature du client. |
| `Intitule_client` | `nvarchar(100)` | RGPD | Intitulé sur 32. |
| `ID_demande_imhoweb` | `nvarchar(10)` |  | Identifiant unique de la demande de logement imhoweb. |
| `Code_departement` | `nvarchar(3)` |  | Code de nomenclature du département. |
| `ID_patrimoine` | `nvarchar(20)` |  | Identifiant unique du patrimoine. |
| `Code_niveau_patrimoine_1` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `ID_organisation` | `nvarchar(20)` |  | Identifiant unique de l'organisation. |
| `Code_niveau_organisation_1` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 1. |
| `Code_niveau_organisation_2` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 2. |
| `Code_niveau_organisation_3` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 3. |
| `Date_debut_occupation` | `date` |  | Date de debut de l'occupation. |
| `Date_fin_occupation` | `date` |  | Date de fin de l'occupation. |
| `Nombre_de_personne` | `int` | RGPD | Nombre de personne. |
| `Code_categorie_menage` | `nvarchar(4)` | RGPD | Code de nomenclature de la catégorie du ménage. |
| `Nom_stockage_document` | `nvarchar(50)` | RGPD | Nom stockage du document. |
| `Indicateur_document_demandeur_etat_civil` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du demandeur de logement de l'état civil. |
| `Nombre_document_demandeur_etat_civil` | `int` | RGPD | Nombre du document du demandeur de logement de l'état civil. |
| `Indicateur_document_demandeur_avis_impot` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du demandeur de logement avis impot. |
| `Nombre_document_demandeur_avis_impot` | `int` | RGPD | Nombre du document du demandeur de logement avis impot. |
| `Indicateur_document_demandeur_situation_familiale` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du demandeur de logement situation familiale. |
| `Nombre_document_demandeur_situation_familiale` | `int` | RGPD | Nombre du document du demandeur de logement situation familiale. |
| `Indicateur_document_demandeur_ressource` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du demandeur de logement ressource. |
| `Nombre_document_demandeur_ressource` | `int` | RGPD | Nombre du document du demandeur de logement ressource. |
| `Indicateur_document_demandeur_logement_actuel` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du demandeur de logement du logement actuel. |
| `Nombre_document_demandeur_logement_actuel` | `int` | RGPD | Nombre du document du demandeur de logement du logement actuel. |
| `Indicateur_document_demandeur_motif` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du demandeur de logement du motif. |
| `Nombre_document_demandeur_motif` | `int` | RGPD | Nombre du document du demandeur de logement du motif. |
| `Indicateur_document_locataire_bail` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire du bail. |
| `Nombre_document_locataire_bail` | `int` | RGPD | Nombre du document du locataire du bail. |
| `Indicateur_document_locataire_garant` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire garant. |
| `Nombre_document_locataire_garant` | `int` | RGPD | Nombre du document du locataire garant. |
| `Indicateur_document_locataire_assurance` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire assurance. |
| `Nombre_document_locataire_assurance` | `int` | RGPD | Nombre du document du locataire assurance. |
| `Indicateur_document_locataire_situation_familiale` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire situation familiale. |
| `Nombre_document_locataire_situation_familiale` | `int` | RGPD | Nombre du document du locataire situation familiale. |
| `Indicateur_document_locataire_avis_impot` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire avis impot. |
| `Nombre_document_locataire_avis_impot` | `int` | RGPD | Nombre du document du locataire avis impot. |
| `Indicateur_document_locataire_avis_echeance` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire avis échéance. |
| `Nombre_document_locataire_avis_echeance` | `int` | RGPD | Nombre du document du locataire avis échéance. |
| `Indicateur_document_locataire_rib` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire rib. |
| `Nombre_document_locataire_rib` | `int` | RGPD | Nombre du document du locataire rib. |
| `Indicateur_document_locataire_caf` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire caf. |
| `Nombre_document_locataire_caf` | `int` | RGPD | Nombre du document du locataire caf. |
| `Indicateur_document_locataire_courrier` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire du courrier. |
| `Nombre_document_locataire_courrier` | `int` | RGPD | Nombre du document du locataire du courrier. |
| `Indicateur_document_locataire_etat_des_lieux` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) du document du locataire de l'état des lieux. |
| `Nombre_document_locataire_etat_des_lieux` | `int` | RGPD | Nombre du document du locataire de l'état des lieux. |
| `Indicateur_anomalie_critique_demandeur` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) de l'anomalie detectee critique du demandeur de logement. |
| `Nombre_anomalie_critique_demandeur` | `int` | RGPD | Nombre de l'anomalie detectee critique du demandeur de logement. |
| `Indicateur_anomalie_moderee_demandeur` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) de l'anomalie detectee moderee du demandeur de logement. |
| `Nombre_anomalie_moderee_demandeur` | `int` | RGPD | Nombre de l'anomalie detectee moderee du demandeur de logement. |
| `Indicateur_anomalie_critique_locataire` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) de l'anomalie detectee critique du locataire. |
| `Nombre_anomalie_critique_locataire` | `int` | RGPD | Nombre de l'anomalie detectee critique du locataire. |
| `Indicateur_anomalie_moderee_locataire` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) de l'anomalie detectee moderee du locataire. |
| `Nombre_anomalie_moderee_locataire` | `int` | RGPD | Nombre de l'anomalie detectee moderee du locataire. |
| `Indicateur_anomalie_critique` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) de l'anomalie detectee critique. |
| `Nombre_anomalie_critique` | `int` | RGPD | Nombre de l'anomalie detectee critique. |
| `Liste_document_manquant_critique` | `nvarchar(200)` |  | NB DOC DDL AVIS IMP. |
| `Indicateur_anomalie_moderee` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) de l'anomalie detectee moderee. |
| `Nombre_anomalie_moderee` | `int` | RGPD | Nombre de l'anomalie detectee moderee. |
| `Date_actualisation` | `datetime` |  | Récupération de ces données depuis la base CAP stockée sur STG. |


### DWH_Enquete_nouveaux_entrants

*Bail et locataire · 37 colonnes*

Enquetes réalisées auprès des nouveaux entrants dans le parc.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `Horodateur` | `datetime` |  | Horodateur. |
| `Libelle_satisfaction_conditions_entree` | `nvarchar(25)` |  | Libellé en clair de la satisfaction conditions d'entree dans les lieux. |
| `Indicateur_satisfaction_conditions_entree` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction conditions d'entree dans les lieux. |
| `Libelle_satisfaction_logement` | `nvarchar(25)` |  | Libellé en clair de la satisfaction du logement. |
| `Indicateur_satisfaction_logement` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction du logement. |
| `Libelle_satisfaction_avant_remise_cles_accompagnement` | `nvarchar(25)` |  | Libellé en clair de la satisfaction avant remise clés accompagnement. |
| `Indicateur_satisfaction__avant_remise_cles_accompagnement` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction avant remise clés accompagnement. |
| `Libelle_satisfaction_remise_cles_signature` | `nvarchar(25)` |  | Libellé en clair de la satisfaction remise clés signature. |
| `Indicateur_satisfaction_remise_cles_signature` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction remise clés signature. |
| `Libelle_satisfaction_remise_cles` | `nvarchar(25)` |  | Libellé en clair de la satisfaction remise clés. |
| `Indicateur_satisfaction_remise_cles` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction remise clés. |
| `Libelle_satisfaction_remise_cles_equipements` | `nvarchar(25)` |  | Libellé en clair de la satisfaction remise clés équipements. |
| `Indicateur_satisfaction_remise_cles_equipements` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction remise clés équipements. |
| `Libelle_lieu_remise_cles` | `nvarchar(25)` |  | Libellé en clair lieu remise clés. |
| `Indicateur_connaissance_ecoute_sante` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) connaissance ecoute sante. |
| `Indicateur_connaissance_assurance_habitation_solidaire` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) connaissance assurance habitation solidaire. |
| `Indicateur_connaissance_materiel_medical_tarif_reduit` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) connaissance materiel medical tarif reduit. |
| `Indicateur_connaissance_fonds_soutien_initiatives_locales` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) connaissance fonds soutien initiatives locales. |
| `Libelle_satisfaction_etat_logement` | `nvarchar(25)` |  | Libellé en clair de la satisfaction de l'état du logement. |
| `Indicateur_satisfaction_proprete_sanitaires_pieces_eau` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction proprete sanitaires pièces eau. |
| `Indicateur_satisfaction_proprete_bouches_air_VMC` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction proprete bouches air vmc. |
| `Indicateur_satisfaction_fonctionnement_portes_serrures_volets` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction fonctionnement portes serrures volets. |
| `Indicateur_satisfaction_fonctionnement_clés_boite_aux_lettres` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction fonctionnement clés boite aux lettres. |
| `Indicateur_satisfaction_fonctionnement_prises_eclairage` | `nvarchar(3)` | RGPD | Indicateur (valeur booléenne ou O/N) de la satisfaction fonctionnement prises eclairage. |
| `Indicateur_satisfaction_fonctionnement_bouches_air_VMC` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction fonctionnement bouches air vmc. |
| `Indicateur_satisfaction_fonctionnement_robinetterie_sanitaires` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction fonctionnement robinetterie sanitaires. |
| `Indicateur_signalement_problème` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) signalement problème. |
| `Libelle_satisfaction_fonctionnement_equipements` | `nvarchar(25)` |  | Libellé en clair de la satisfaction fonctionnement équipements. |
| `Indicateur_satisfaction_fonctionnement_equipements` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de la satisfaction fonctionnement équipements. |
| `Libelle_utilisation_equipement_chauffage` | `nvarchar(50)` | RGPD | Libellé en clair de l'utilisation de l'équipement technique du chauffage. |
| `Libelle_utilisation_equipement_eau_chaude` | `nvarchar(50)` |  | Libellé en clair de l'utilisation de l'équipement technique eau chaude. |
| `Libelle_utilisation_equipement_appareils_electrique` | `nvarchar(50)` |  | Libellé en clair de l'utilisation de l'équipement technique appareils electrique. |
| `Libelle_departement` | `nvarchar(50)` |  | Libellé en clair du département. |
| `Libelle_agence` | `nvarchar(50)` | RGPD | Libellé en clair de l'agence. |
| `ID_questionnaire` | `nvarchar(max)` |  | Identifiant unique questionnaire. |
| `Code_niveau_patrimoine_1` | `nvarchar(max)` |  | Retourne la chaîne entière si aucun chiffré n'est trouvé. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Enquete_satisfaction_envoi

*Bail et locataire · 10 colonnes*

Envois d'enquetes de satisfaction aux clients.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client` | `nvarchar(10)` | NN RGPD | Identifiant unique du client. |
| `ID_lot` | `nvarchar(10)` | NN | Identifiant unique du lot (unité de gestion IKOS). |
| `ID_client_enquete` | `nvarchar(50)` | NN RGPD | Identifiant unique du client de l'enquete. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_client` | `nvarchar(6)` | RGPD | Code de nomenclature du client. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Code_enquete` | `nvarchar(25)` |  | Code de nomenclature de l'enquete. |
| `Libelle_enquete` | `nvarchar(200)` |  | Libellé en clair de l'enquete. |
| `Date_envoi` | `date` |  | Date réalisation. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Equipement

*Patrimoine · 36 colonnes*

Référentiel des équipements techniques installes sur le patrimoine et dans les lots.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_equipement` | `nvarchar(20)` |  | Récupération directe des données depuis ODS.Aiguillon_Equipement. |
| `ID_patrimoine_lot` | `nvarchar(20)` |  | Identifiant unique du patrimoine du lot (unité de gestion IKOS). |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_niveau_patrimoine_1` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Niveau_patrimoine_lot_rattachement` | `nvarchar(50)` |  | Niveau du patrimoine du lot (unité de gestion IKOS) rattachement. |
| `Code_famille_equipement` | `nvarchar(10)` |  | Code de nomenclature de la famille de l'équipement technique. |
| `Libelle_famille_equipement` | `nvarchar(255)` |  | Libellé en clair de la famille de l'équipement technique. |
| `Code_type_equipement` | `nvarchar(10)` |  | Code de nomenclature du type de l'équipement technique. |
| `Libelle_type_equipement` | `nvarchar(255)` |  | Libellé en clair du type de l'équipement technique. |
| `Code_nature_equipement` | `nvarchar(10)` |  | Code de nomenclature de la nature de l'équipement technique. |
| `Libelle_nature_equipement` | `nvarchar(255)` |  | Libellé en clair de la nature de l'équipement technique. |
| `Code_materiaux_equipement` | `nvarchar(10)` |  | Code de nomenclature matériaux de l'équipement technique. |
| `Libelle_materiaux_equipement` | `nvarchar(255)` |  | Libellé en clair matériaux de l'équipement technique. |
| `Libelle_emplacement` | `nvarchar(255)` |  | Libellé en clair emplacement. |
| `Indicateur_pseudo_equipement` | `varchar(3)` | NN | Indicateur (valeur booléenne ou O/N) pseudo de l'équipement technique. |
| `ID_equipement_rattachement` | `nvarchar(20)` |  | Identifiant unique de l'équipement technique rattachement. |
| `Unite_principale` | `nvarchar(10)` |  | Quantités. |
| `Quantite_nombre` | `int` | RGPD | Quantité du nombre. |
| `Quantite_surface` | `decimal(10,2)` |  | Quantité de la surface. |
| `Quantite_lineaire` | `decimal(10,2)` |  | Code unité. |
| `Indicateur_activite` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de l'activite d'exécution. |
| `Date_installation` | `date` |  | Cycle de vie. |
| `Date_mise_en_service` | `date` |  | Date de mise en service. |
| `Date_fin_de_service` | `date` |  | Date de fin d'en service. |
| `Marque` | `nvarchar(255)` |  | Marque d'équipement. |
| `Modele` | `nvarchar(255)` |  | Modèle d'équipement. |
| `Puissance` | `nvarchar(255)` |  | Puissance d'équipement. |
| `Capacite` | `nvarchar(255)` |  | Capacité d'équipement. |
| `Mode_fonctionnement` | `nvarchar(255)` |  | Mode fonctionnement. |
| `Numero_serie_constructeur` | `nvarchar(255)` |  | Numéro série constructeur. |
| `Indicateur_iot` | `nvarchar(255)` |  | Indicateur (valeur booléenne ou O/N) iot. |
| `Numero_serie_boitier_iot` | `nvarchar(255)` |  | Numéro série boitier iot. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Equipement_OLD

*Patrimoine · 31 colonnes*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_equipement` | `nvarchar(20)` |  | Identifiant unique de l'équipement technique. |
| `ID_patrimoine_lot` | `nvarchar(20)` |  | Identifiant unique du patrimoine du lot (unité de gestion IKOS). |
| `Niveau_patrimoine_lot` | `nvarchar(50)` |  | Niveau du patrimoine du lot (unité de gestion IKOS). |
| `Code_famille_equipement` | `nvarchar(10)` |  | Code de nomenclature de la famille de l'équipement technique. |
| `Libelle_famille_equipement` | `nvarchar(255)` |  | Libellé en clair de la famille de l'équipement technique. |
| `Code_type_equipement` | `nvarchar(10)` |  | Code de nomenclature du type de l'équipement technique. |
| `Libelle_type_equipement` | `nvarchar(255)` |  | Libellé en clair du type de l'équipement technique. |
| `Code_nature_equipement` | `nvarchar(10)` |  | Code de nomenclature de la nature de l'équipement technique. |
| `Libelle_nature_equipement` | `nvarchar(255)` |  | Libellé en clair de la nature de l'équipement technique. |
| `Code_materiaux_equipement` | `nvarchar(10)` |  | Code de nomenclature matériaux de l'équipement technique. |
| `Libelle_materiaux_equipement` | `nvarchar(255)` |  | Libellé en clair matériaux de l'équipement technique. |
| `Libelle_emplacement` | `nvarchar(255)` |  | Libellé en clair emplacement. |
| `Indicateur_pseudo_equipement` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) pseudo de l'équipement technique. |
| `ID_equipement_rattachement` | `nvarchar(20)` |  | Identifiant unique de l'équipement technique rattachement. |
| `Unite_principale` | `nvarchar(10)` |  | Unité de mesure principale. |
| `Quantite_nombre` | `int` | RGPD | Quantité du nombre. |
| `Quantite_surface` | `decimal(10,2)` |  | Quantité de la surface. |
| `Quantite_lineaire` | `decimal(10,2)` |  | Quantité lineaire. |
| `Indicateur_activite` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de l'activite d'exécution. |
| `Date_installation` | `date` |  | Date installation. |
| `Date_mise_en_service` | `date` |  | Date de mise en service. |
| `Date_fin_de_service` | `date` |  | Date de fin d'en service. |
| `Marque` | `nvarchar(255)` |  | Marque d'équipement old. |
| `Modele` | `nvarchar(255)` |  | Modèle d'équipement old. |
| `Puissance` | `nvarchar(255)` |  | Puissance d'équipement old. |
| `Capacite` | `nvarchar(255)` |  | Capacité d'équipement old. |
| `Mode_fonctionnement` | `nvarchar(255)` |  | Mode fonctionnement. |
| `Numero_serie_constructeur` | `nvarchar(255)` |  | Numéro série constructeur. |
| `Indicateur_iot` | `nvarchar(255)` |  | Indicateur (valeur booléenne ou O/N) iot. |
| `Numero_serie_boitier_iot` | `nvarchar(255)` |  | Numéro série boitier iot. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Geographie

*Référentiel · 13 colonnes · PK : `Code_INSEE_commune`*

Dimension géographique : communes, codes INSEE, découpages administratifs et statistiques.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `Code_INSEE_commune` | `nvarchar(5)` | PK NN | Code de nomenclature INSEE de la commune. |
| `Libelle_commune` | `nvarchar(255)` |  | Libellé en clair de la commune. |
| `Code_departement` | `nvarchar(3)` |  | Code de nomenclature du département. |
| `Libelle_departement` | `nvarchar(255)` |  | Libellé du département. |
| `Code_region` | `nvarchar(2)` |  | Code de nomenclature de la region. |
| `Code_EPCI` | `nvarchar(9)` |  | Code de nomenclature de l'EPCI (intercommunalite). |
| `Nature_EPCI` | `nvarchar(10)` |  | Nature EPCI : nature de l'EPCI (intercommunalite). |
| `Libelle_EPCI` | `nvarchar(255)` |  | Libellé en clair de l'EPCI (intercommunalite). |
| `Zonage_1_2_3` | `nvarchar(50)` | RGPD | Gestion des zonages. |
| `Zonage_ABC` | `nvarchar(50)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom Zonage_ABC. en vigueur. |
| `Zonage_TLV` | `nvarchar(50)` | RGPD | Champ source repris tel quel dans l'entrepôt sous le nom Zonage_TLV. |
| `Zonage_ZRR_FRR` | `nvarchar(50)` | RGPD | Zonage ZRR et FRR. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Geographie_PxM2

*Référentiel · 6 colonnes · PK : `Id_Geographie_PxM2`*

Prix au metre carre par maille géographique, utilisé pour les études de valorisation.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `Id_Geographie_PxM2` | `int` | PK NN | Identifiant unique de la géographie prix m2. |
| `Code_INSEE_commune` | `nvarchar(5)` | NN | Code de nomenclature INSEE de la commune. |
| `Libelle_Quartier` | `nvarchar(255)` |  | Libellé en clair du quartier. |
| `Type_Bien` | `nvarchar(20)` |  | Type bien. |
| `Prix_M2` | `decimal(15,2)` |  | Prix M2. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Intervention

*Technique et maintenance · 20 colonnes · PK : `ID_intervention`*

Interventions techniques et de maintenance réalisées sur le patrimoine.

Jointures : `ID_commande` → `DWH.Commande.ID_commande` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_intervention` | `varchar(15)` | PK NN | Identifiant unique d’intervention : concatène le code société et le numéro d’intervention. |
| `ID_commande` | `varchar(15)` |  | Référence à la commande (FK vers la table Commandes). |
| `ID_lot` | `varchar(15)` |  | Référence au lot. |
| `Numero_intervention` | `varchar(10)` |  | Numéro d’intervention. |
| `Code_lot_intervention` | `varchar(6)` |  | Code du lot lié à l’intervention. |
| `Code_intervention` | `varchar(8)` |  | Code de l’intervention standard. |
| `Libelle_intervention` | `varchar(255)` |  | Libellé de l’intervention. |
| `Date_realisation_intervention` | `date` |  | Date de réalisation de l'intervention. |
| `Date_enregistrement_commande` | `date` |  | Date d'enregistrement de la commande associée. |
| `Quantite` | `decimal(10,2)` |  | Quantité d'intervention. |
| `Unite` | `varchar(10)` |  | Unité de mesure d'intervention. |
| `Prix_unitaire_HT` | `decimal(15,2)` |  | Prix unitaire HT. |
| `Montant_total_HT` | `decimal(15,2)` |  | Montant en euros total hors taxes. |
| `Prix_unitaire_TVA` | `decimal(15,2)` |  | Montant TVA. |
| `Montant_total_TTC` | `decimal(15,2)` |  | Montant en euros total toutes taxes comprises. |
| `Code_schema_comptable` | `varchar(10)` |  | Code de nomenclature du schéma comptable. |
| `Livrable_attendu` | `varchar(10)` |  | Livrable attendu. |
| `Date_realisation_livrable` | `date` |  | Date de disponibilité du livrable. |
| `Indicateur_livrable_valide` | `varchar(3)` |  | Indicateur livrable présent (si le livrable a été réalisé à +/- 6 mois de la commande alors 'Oui' sinon 'Non'. |
| `Date_actualisation` | `datetime` | NN | Date d'actualisation des données. |


### DWH_Lot

*Patrimoine · 51 colonnes · PK : `ID_lot`*

Dimension des lots (unités de gestion IKOS) : logements, stationnements, commerces et dépendances, avec leurs caracteristiques physiques, réglementaires et commerciales.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client_lot` | `nvarchar(30)` | NN RGPD | Identifiant unique du client du lot (unité de gestion IKOS). |
| `ID_lot` | `nvarchar(10)` | PK NN | Identifiant unique du lot (unité de gestion IKOS). |
| `ID_patrimoine` | `nvarchar(20)` |  | Identifiant unique du patrimoine. |
| `ID_RPLS` | `nvarchar(20)` |  | Identifiant unique du RPLS (répertoire des logements locatifs des bailleurs sociaux). |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Code_niveau_patrimoine_1` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `Libelle_activite_lot` | `nvarchar(50)` |  | Libellé en clair de l'activite d'exécution du lot (unité de gestion IKOS). |
| `Libelle_usage_lot` | `nvarchar(50)` | RGPD | Libellé en clair de l'usage du lot (unité de gestion IKOS). |
| `Code_nature_lot` | `nvarchar(3)` |  | Code de nomenclature de la nature du lot (unité de gestion IKOS). |
| `Libelle_nature_lot` | `nvarchar(50)` |  | Libellé en clair de la nature du lot (unité de gestion IKOS). |
| `Code_partie_commune_privative` | `nvarchar(5)` |  | Code parties communes et privatives. |
| `Libelle_partie_commune_privative` | `nvarchar(50)` |  | Libellé parties communes et privatives. |
| `Etage` | `int` | RGPD | Code étage. |
| `Numero_porte` | `nvarchar(10)` |  | Numéro de la porte. |
| `Rang_numero_porte_par_etage` | `int` | RGPD | Rang du numéro porte par étage. |
| `Code_individuel_collectif` | `nvarchar(3)` |  | Code ind/collectif. |
| `Libelle_individuel_collectif` | `nvarchar(50)` |  | Libl ind/collectif. |
| `Code_categorie_financement` | `nvarchar(3)` |  | Code de nomenclature de la catégorie du financement. |
| `Libelle_categorie_financement` | `nvarchar(50)` |  | Libellé en clair de la catégorie du financement. |
| `Code_type_lot` | `nvarchar(3)` |  | Code de nomenclature du type du lot (unité de gestion IKOS). |
| `Libelle_type_lot` | `nvarchar(50)` |  | Libellé en clair du type du lot (unité de gestion IKOS). |
| `Code_niveau_adaptation` | `nvarchar(5)` |  | Code de nomenclature du niveau de l'adaptation du logement. |
| `Libelle_niveau_adaptation` | `nvarchar(50)` |  | Libellé en clair du niveau de l'adaptation du logement. |
| `Indicateur_niveau_adaptation_partie_commune` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) du niveau de l'adaptation du logement partie de la commune. |
| `Indicateur_niveau_adaptation_partie_privative_public_cible` | `nvarchar(150)` |  | Indicateur (valeur booléenne ou O/N) du niveau de l'adaptation du logement partie privative public de la cibl… |
| `Indicateur_niveau_adaptation_partie_privative_service` | `nvarchar(150)` |  | Indicateur (valeur booléenne ou O/N) du niveau de l'adaptation du logement partie privative en service. |
| `Code_niveau_adaptation_classification_USH` | `nvarchar(10)` |  | Code de nomenclature du niveau de l'adaptation du logement classification ush. |
| `Code_niveau_adaptation_classification_ARO` | `nvarchar(10)` |  | Code de nomenclature du niveau de l'adaptation du logement classification aro. |
| `Code_niveau_adaptation_classification_RPLS` | `nvarchar(10)` |  | Code de nomenclature du niveau de l'adaptation du logement classification du RPLS (répertoire des logements l… |
| `Code_niveau_adaptation_classification_Rennes_Metropole` | `nvarchar(10)` |  | Code de nomenclature du niveau de l'adaptation du logement classification rennes metropole. |
| `Surface_habitable` | `decimal(8,2)` |  | Surface en metrès carrés habitable. |
| `Nombre_chambres` | `int` | RGPD | Nombre de chambres. |
| `Date_construction` | `date` |  | Date de construction - conversion au format date. |
| `Date_reception_travaux` | `date` |  | Date reception des travaux. |
| `Date_livraison` | `date` |  | Date de livraison. |
| `Date_mise_en_service` | `date` |  | Date de mise en service. |
| `Nombre_jours_depuis_mise_en_service` | `int` | RGPD | Nombre de jours depuis mise en service. |
| `Date_debut_commercialisation` | `date` |  | Date de debut de la commercialisation. |
| `Indicateur_debut_commercialisation` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) de debut de la commercialisation. |
| `Nombre_baux_lot` | `int` | RGPD | Nombre de baux. |
| `Indicateur_premiere_mise_en_location` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) première de mise en location. |
| `Indicateur_fin_gestion` | `nvarchar(5)` |  | Indicateur fin de gestion. |
| `Code_etat_actuel` | `nvarchar(3)` |  | Code de nomenclature de l'état actuel. |
| `Libelle_etat_actuel` | `nvarchar(50)` |  | Libellé en clair de l'état actuel. |
| `Indicateur_exploitation` | `nvarchar(3)` |  | Activité. |
| `Indicateur_disponibilite_commercialisation` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) disponibilite de la commercialisation. |
| `Lien_IKOS_synthese_lot` | `nvarchar(2048)` |  | Lien IKOS vers la synthèse du lot. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Lot_historique

*Patrimoine · 63 colonnes · PK : `ID_lot_annee_mois`*

Historisation mensuelle des lots, permettant de reconstituer l'état du parc à une date passee.

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un) ; `Date_mise_en_service` → `DWH.Calendrier.Date` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_lot` | `nvarchar(10)` |  | Identifiant unique du lot (unité de gestion IKOS). |
| `ID_lot_annee_mois` | `nvarchar(20)` | PK NN | Identifiant unique du lot (unité de gestion IKOS) de l'annee en mois. |
| `ID_patrimoine` | `nvarchar(20)` |  | Identifiant unique du patrimoine. |
| `Annee_mois` | `nvarchar(7)` |  | Annee en mois. |
| `Annee_mois_ordre` | `int` |  | Annee en mois de l'ordre. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Code_niveau_patrimoine_1` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `Libelle_activite_lot` | `nvarchar(50)` |  | Libellé en clair de l'activite d'exécution du lot (unité de gestion IKOS). |
| `Libelle_usage_lot` | `nvarchar(50)` | RGPD | Libellé en clair de l'usage du lot (unité de gestion IKOS). |
| `Code_nature_lot` | `nvarchar(3)` |  | Code de nomenclature de la nature du lot (unité de gestion IKOS). |
| `Libelle_nature_lot` | `nvarchar(50)` |  | Libellé en clair de la nature du lot (unité de gestion IKOS). |
| `Code_partie_commune_privative` | `nvarchar(5)` |  | IND PP/PC. |
| `Libelle_partie_commune_privative` | `nvarchar(50)` |  | IND PP/PC. |
| `Etage` | `nvarchar(50)` | RGPD | Code étage. |
| `Numero_porte` | `nvarchar(50)` |  | Numéro de la porte. |
| `Code_individuel_collectif` | `nvarchar(3)` |  | Code ind/collectif. |
| `Libelle_individuel_collectif` | `nvarchar(50)` |  | Libl ind/collectif. |
| `Code_categorie_financement` | `nvarchar(3)` |  | Code de nomenclature de la catégorie du financement. |
| `Libelle_categorie_financement` | `nvarchar(50)` |  | Libellé en clair de la catégorie du financement. |
| `Code_type_lot` | `nvarchar(3)` |  | Code de nomenclature du type du lot (unité de gestion IKOS). |
| `Libelle_type_lot` | `nvarchar(50)` |  | Libellé en clair du type du lot (unité de gestion IKOS). |
| `Indicateur_accessibilite_PMR` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) de l'accessibilité pmr. |
| `Code_niveau_adaptation` | `nvarchar(5)` |  | Code de nomenclature du niveau de l'adaptation du logement. |
| `Surface_habitable` | `decimal(8,2)` |  | Surface en metrès carrés habitable. |
| `Nombre_chambres` | `int` | RGPD | Nombre de chambres. |
| `Date_construction` | `date` |  | Date de construction. |
| `Date_reception_travaux` | `date` |  | Date reception des travaux. |
| `Date_livraison` | `date` |  | Date de livraison. |
| `Date_declaration_achevement_travaux` | `date` |  | DAT REEL. |
| `Date_mise_en_service` | `date` |  | Date de mise en service. |
| `Nombre_jours_depuis_mise_en_service` | `int` | RGPD | Nombre en jours depuis le mise en service. |
| `Date_debut_commercialisation` | `date` |  | Date de debut de la commercialisation. |
| `Code_etat` | `nvarchar(3)` |  | Code de nomenclature de l'état. |
| `Libelle_etat` | `nvarchar(50)` |  | Libellé en clair de l'état. |
| `Indicateur_changement_etat` | `int` |  | Indicateur (valeur booléenne ou O/N) changement de l'état. |
| `Nombre_changement_etat_annee_N` | `int` | RGPD | Nombre changement de l'état de l'annee n. |
| `Nombre_changement_etat_12_derniers_mois` | `int` | RGPD | Nombre changement de l'état de niveau 12 derniers en mois. |
| `Indicateur_exploitation` | `nvarchar(3)` |  | Activité. |
| `Indicateur_disponibilite_commercialisation` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) disponibilite de la commercialisation. |
| `Indicateur_propriete` | `nvarchar(3)` |  | Indicateur (valeur booléenne ou O/N) propriété. |
| `Nombre_entree` | `int` | RGPD | Nombre d'entree dans les lieux. |
| `Nombre_entree_annee_N` | `int` | RGPD | Nombre d'entree dans les lieux de l'annee n. |
| `Nombre_entree_12_derniers_mois` | `int` | RGPD | Nombre d'entree dans les lieux de niveau 12 derniers en mois. |
| `Nombre_sortie` | `int` | RGPD | Nombre de sortie des lieux. |
| `Nombre_sortie_annee_N` | `int` | RGPD | Nombre de sortie des lieux de l'annee n. |
| `Nombre_sortie_12_derniers_mois` | `int` | RGPD | Nombre de sortie des lieux de niveau 12 derniers en mois. |
| `Nombre_entree_mutation` | `int` | RGPD | Nombre d'entree dans les lieux de la mutation. |
| `Nombre_entree_mutation_annee_N` | `int` | RGPD | Nombre d'entree dans les lieux de la mutation de l'annee n. |
| `Nombre_entree_mutation_12_derniers_mois` | `int` | RGPD | Nombre d'entree dans les lieux de la mutation de niveau 12 derniers en mois. |
| `Nombre_sortie_mutation` | `int` | RGPD | Nombre de sortie des lieux de la mutation. |
| `Nombre_sortie_mutation_annee_N` | `int` | RGPD | Nombre de sortie des lieux de la mutation de l'annee n. |
| `Nombre_sortie_mutation_12_derniers_mois` | `int` | RGPD | Nombre de sortie des lieux de la mutation de niveau 12 derniers en mois. |
| `Nombre_jours_vacance` | `int` | RGPD | Nombre en jours de la vacance locative. |
| `Nombre_jours_vacance_annee_N` | `int` | RGPD | Nombre en jours de la vacance locative de l'annee n. |
| `Nombre_jours_vacance_12_derniers_mois` | `int` | RGPD | Nombre en jours de la vacance locative de niveau 12 derniers en mois. |
| `Montant_perte_financiere` | `decimal(8,2)` |  | Mt pertes 1  fam rub 1. |
| `Montant_perte_financiere_annee_N` | `decimal(8,2)` |  | Montant en euros perte financiere de l'annee n. |
| `Montant_perte_financiere_12_derniers_mois` | `decimal(8,2)` |  | Montant en euros perte financiere de niveau 12 derniers en mois. |
| `Lien_IKOS_synthese_lot` | `nvarchar(2048)` |  | Organisme. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Occupant

*Bail et locataire · 35 colonnes*

Table des occupants déclarés du logement, au-delà du seul titulaire du bail.

Jointures : `ID_client` → `DWH.Client.ID_client` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_occupant` | `nvarchar(13)` | RGPD | Création de l'ID complet client. |
| `ID_client` | `nvarchar(10)` | RGPD | Identifiant unique du client. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_client` | `nvarchar(6)` | RGPD | Code de nomenclature du client. |
| `Code_occupant` | `nvarchar(10)` | RGPD | Code de nomenclature de l'occupant du logement. |
| `Date_debut_rattachement_client` | `date` | RGPD | Date de début de rattachement. |
| `Date_fin_rattachement_client` | `date` | RGPD | Date de fin de rattachement. |
| `Indicateur_rattachement_client` | `nvarchar(5)` | RGPD | Indicateur de rattachement au client. |
| `Indicateur_rattachement_menage` | `nvarchar(5)` | RGPD | Indicateur de rattachement au ménage. |
| `Qualification_occupant` | `nvarchar(24)` | RGPD | Retraitement du type contractant. |
| `Indicateur_rattachement_fiscal` | `nvarchar(5)` |  | Retraitement du rattachement fiscal. |
| `Indicateur_garde_alternee` | `nvarchar(5)` |  | Ind garde alternée. |
| `Indicateur_droit_de_visite` | `nvarchar(5)` |  | Ind droit de visite. |
| `Indicateur_carte_mobilite_inclusion` | `nvarchar(5)` |  | Ind carte mobilité. |
| `Type_personne` | `nvarchar(24)` |  | Variables informations. |
| `Code_forme_juridique_occupant` | `nvarchar(6)` | RGPD | Code titre. |
| `Libelle_forme_juridique_occupant` | `nvarchar(50)` | RGPD | Ind pers. |
| `Libelle_titre_occupant` | `nvarchar(50)` | RGPD | Libellé en clair titre de l'occupant du logement. |
| `Raison_sociale_occupant` | `nvarchar(50)` | RGPD | Code titre. |
| `Code_titre_occupant` | `nvarchar(13)` | RGPD | Code de nomenclature titre de l'occupant du logement. |
| `Nom_occupant` | `nvarchar(50)` | RGPD | Nom de l'occupant du logement. |
| `Prenom_occupant` | `nvarchar(50)` | RGPD | Prenom de l'occupant du logement. |
| `Age_occupant` | `nvarchar(3)` | RGPD | Date naissance/création. |
| `Classe_age_occupant` | `nvarchar(50)` | RGPD | Date naissance/création. |
| `Majorite_occupant` | `nvarchar(24)` | RGPD | Date naissance/création. |
| `Date_naissance_occupant` | `date` | RGPD | Date naissance de l'occupant du logement. |
| `Date_deces_occupant` | `date` | RGPD | Date deces de l'occupant du logement. |
| `Sexe_occupant` | `nvarchar(2)` | RGPD | Code sexe. |
| `Indicateur_revenus_imposables_occupant` | `nvarchar(5)` | RGPD | Année ressources. |
| `Annee_revenus_imposables_occupant` | `nvarchar(4)` | RGPD | Année ressources. |
| `Montant_revenus_imposables_occupant` | `decimal(12,2)` | RGPD | Montant ressources. |
| `Situation_famille_occupant` | `nvarchar(50)` | RGPD | Code situation famille. |
| `Libelle_detail_lien_rattachement` | `nvarchar(24)` |  | Libellé détail lien tiers. |
| `Code_occupant_de_rattachement` | `nvarchar(10)` | RGPD | Code de nomenclature de l'occupant du logement de rattachement. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Organisation

*Organisation · 10 colonnes · PK : `ID_organisation`*

Dimension organisationnelle : découpage hiérarchique des entites du groupe.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_organisation` | `nvarchar(20)` | PK NN | Identifiant unique de l'organisation. |
| `Niveau_organisation` | `nvarchar(20)` |  | Niveau de l'organisation. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_niveau_organisation_1` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 1. |
| `Code_niveau_organisation_2` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 2. |
| `Code_niveau_organisation_3` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 3. |
| `Libelle_organisation` | `nvarchar(24)` |  | Libellé en clair de l'organisation. |
| `Adresse` | `nvarchar(32)` | RGPD | Adresse d'organisation. |
| `Indicateur_validite` | `nvarchar(3)` |  | Ajout d'une information sémantique pour l'indicateur de validité. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Organisation_patrimoine_pivot

*Patrimoine · 3 colonnes · PK : `ID_organisation, ID_patrimoine`*

Jointures : `ID_patrimoine` → `DWH.Patrimoine.ID_patrimoine` (plusieurs vers un) ; `ID_organisation` → `DWH.Organisation.ID_organisation` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_organisation` | `nvarchar(20)` | PK NN | Identifiant unique de l'organisation. |
| `ID_patrimoine` | `varchar(20)` | PK NN | Identifiant unique du patrimoine. |
| `Date_actualisation` | `datetime` | NN | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Patrimoine

*Patrimoine · 31 colonnes · PK : `ID_patrimoine`*

Dimension decrivant l'ensemble des patrimoines (sites, résidences, bâtiments, cages d'escalier, stationnements) rattaches aux entites de l'UES Aiguillon.

Jointures : `Code_INSEE_commune` → `DWH.Geographie.Code_INSEE_commune` (plusieurs vers un) ; `Date_construction` → `DWH.Calendrier.Date` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_patrimoine` | `nvarchar(20)` | PK NN | Identifiant unique du patrimoine. |
| `ID_organisation` | `nvarchar(20)` |  | Identifiant unique de l'organisation. |
| `Niveau_patrimoine` | `nvarchar(50)` |  | Niveau du patrimoine. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_niveau_patrimoine_1` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_niveau_patrimoine_2` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 2. |
| `Code_niveau_patrimoine_3` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 3. |
| `Libelle_patrimoine` | `nvarchar(255)` |  | Libellé en clair du patrimoine. |
| `Code_niveau_organisation_1` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 1. |
| `Code_niveau_organisation_2` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 2. |
| `Code_niveau_organisation_3` | `nvarchar(4)` |  | Code de nomenclature du niveau de l'organisation de niveau 3. |
| `Libelle_organisation` | `nvarchar(255)` |  | Libellé en clair de l'organisation. |
| `Adresse_complete` | `nvarchar(500)` | RGPD | Adresse rue. |
| `Adresse` | `nvarchar(255)` | RGPD | Adresse de patrimoine. |
| `Libelle_commune` | `nvarchar(255)` |  | Libellé en clair de la commune. |
| `Code_postal` | `nvarchar(5)` |  | Code de nomenclature postal. |
| `Code_INSEE_commune` | `nvarchar(5)` |  | Code de nomenclature INSEE de la commune. |
| `Latitude` | `nvarchar(11)` |  | Latitude (coordonnee géographique) de patrimoine. |
| `Longitude` | `nvarchar(11)` |  | Longitude (coordonnee géographique) de patrimoine. |
| `Code_département` | `nvarchar(3)` |  | Code de nomenclature du département. |
| `Code_bassin_habitat` | `nvarchar(3)` |  | Code bassin d'habitat. |
| `Code_quartier` | `nvarchar(5)` |  | Code de nomenclature du quartier. |
| `Date_construction` | `date` |  | Date de construction - conversion au format date. |
| `Mode_acquisition` | `nvarchar(50)` |  | Libellé mode acquisition. |
| `Date_acquisition` | `date` |  | Date d'acquisition - conversion au format date. |
| `Indicateur_annulation` | `nvarchar(3)` |  | Ajout d'une information sémantique pour l'indicateur d'annulation. |
| `Date_fin_validite` | `date` |  | Date de fin de validité - conversion au format date. |
| `Lien_IKOS_synthese_patrimoine` | `nvarchar(2048)` |  | Organisme. |
| `Lien_Google_Maps` | `nvarchar(2048)` |  | Adresse rue. |
| `Lien_Google_Earth` | `nvarchar(2048)` |  | Adresse rue. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Patrimoine_lot_pivot

*Patrimoine · 4 colonnes · PK : `ID_lot, ID_patrimoine, ID_patrimoine_lot`*

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un) ; `ID_patrimoine` → `DWH.Patrimoine.ID_patrimoine` (plusieurs vers un) ; `ID_patrimoine_lot` → `DWH.Equipement.ID_patrimoine_lot` (plusieurs vers plusieurs)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_lot` | `nvarchar(10)` | PK NN | Identifiant unique du lot (unité de gestion IKOS). |
| `ID_patrimoine` | `nvarchar(20)` | PK NN | Identifiant unique du patrimoine. |
| `ID_patrimoine_lot` | `nvarchar(20)` | PK NN | Identifiant unique du patrimoine du lot (unité de gestion IKOS). |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Piece

*Patrimoine · 12 colonnes · PK : `ID_piece`*

Pièces composant les logements.

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_piece` | `nvarchar(14)` | PK NN | Identifiant unique de la pièce du logement. |
| `ID_lot` | `nvarchar(10)` |  | Identifiant unique du lot (unité de gestion IKOS). |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Code_piece` | `nvarchar(3)` |  | Code de nomenclature de la pièce du logement. |
| `Libelle_piece` | `nvarchar(50)` |  | Libellé en clair de la pièce du logement. |
| `Libelle_categorie_piece` | `nvarchar(100)` |  | Libellé en clair de la catégorie de la pièce du logement. |
| `Surface_reelle` | `decimal(8,2)` |  | Surface réelle. |
| `Surface_corrigee` | `decimal(8,2)` |  | Surface corrigée. |
| `Surface_reduite` | `decimal(8,2)` |  | Surface réduite. |
| `Code_type_decompte` | `nvarchar(3)` |  | Code de nomenclature du type decompte. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Proposition_logement

*Entrepôt de données · 47 colonnes*

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_proposition_imhoweb` | `nvarchar(24)` |  | Identifiant unique de la proposition de logement imhoweb. |
| `ID_demande_imhoweb` | `nvarchar(24)` |  | Identifiant unique de la demande de logement imhoweb. |
| `ID_demande_unique` | `nvarchar(24)` |  | Identifiant unique de la demande de logement unique. |
| `Code_niveau_patrimoine_1` | `nvarchar(4)` |  | Code de nomenclature du niveau du patrimoine de niveau 1. |
| `Code_lot` | `nvarchar(6)` |  | Code de nomenclature du lot (unité de gestion IKOS). |
| `Code_etat_proposition` | `nvarchar(4)` |  | Code de nomenclature de l'état de la proposition de logement. |
| `Libelle_proposition` | `nvarchar(50)` |  | Libellé en clair de la proposition de logement. |
| `ID_bailleur` | `nvarchar(13)` |  | Identifiant unique bailleur. |
| `Libelle_bailleur` | `nvarchar(50)` |  | Libellé en clair bailleur. |
| `Code_agence` | `nvarchar(4)` | RGPD | Code de nomenclature de l'agence. |
| `Libelle_agence` | `nvarchar(70)` | RGPD | Libellé en clair de l'agence. |
| `Date_creation` | `date` |  | Date de création. |
| `Date_passage_commission` | `date` | RGPD | Date passage de la commission d'attribution (CALS). |
| `Date_accord_commission` | `date` |  | Date accord de la commission d'attribution (CALS). |
| `Date_refus_commission` | `date` |  | Date refus de la commission d'attribution (CALS). |
| `Date_accord_demandeur` | `date` | RGPD | Date accord du demandeur de logement. |
| `Date_refus_demandeur` | `date` | RGPD | Date refus du demandeur de logement. |
| `Libelle_decision_demandeur` | `nvarchar(50)` | RGPD | Libellé en clair decision du demandeur de logement. |
| `Date_transfert_GL` | `date` |  | Date transfert gl. |
| `Date_entree_dans_les_lieux` | `date` |  | Date d'entree dans les lieux dans les lieux. |
| `Libelle_motif_refus_demandeur` | `nvarchar(100)` | RGPD | Libellé en clair du motif refus du demandeur de logement. |
| `Montant_APL` | `decimal(10,2)` |  | Montant en euros de l'APL (aide personnalisee au logement). |
| `Montant_reste_a_vivre` | `decimal(10,2)` |  | Montant en euros reste à vivre. |
| `Montant_RLS` | `decimal(10,2)` |  | Montant en euros rls. |
| `Taux_effort` | `decimal(10,2)` |  | Taux ou pourcentage effort. |
| `Montant_loyer_charge` | `decimal(10,2)` |  | Montant en euros du loyer charge. |
| `Montant_loyer` | `decimal(10,2)` |  | Montant en euros du loyer. |
| `Indicateur_premier_quartile` | `nvarchar(4)` |  | Indicateur (valeur booléenne ou O/N) premier quartile. |
| `Indicateur_QPV` | `nvarchar(5)` |  | Indicateur (valeur booléenne ou O/N) du quartier prioritaire (QPV). |
| `Libelle_QPV` | `nvarchar(70)` |  | Libellé en clair du quartier prioritaire (QPV). |
| `Montant_revenu_unité_consommation` | `decimal(10,2)` | RGPD | Montant en euros revenu unité consommation. |
| `Libelle_EPCI` | `nvarchar(70)` |  | Libellé en clair de l'EPCI (intercommunalite). |
| `Libelle_bailleur_logement` | `nvarchar(50)` |  | Libellé en clair bailleur du logement. |
| `Code_organisme_proposition` | `nvarchar(50)` |  | Code de nomenclature organisme de la proposition de logement. |
| `Libelle_reservataire_proposition` | `nvarchar(50)` |  | Libellé en clair réservataire de la proposition de logement. |
| `Date_entree_dans_les_lieux_prevue` | `date` |  | Date d'entree dans les lieux dans les lieux prévue. |
| `Date_limite_reponse_demandeur` | `date` | RGPD | Date limite reponse du demandeur de logement. |
| `Date_signature_bail` | `date` |  | Date signature du bail. |
| `ID_CAL` | `nvarchar(10)` |  | Identifiant unique commission d'attribution. |
| `ID_designataire_proposition` | `nvarchar(10)` |  | Identifiant unique designataire de la proposition de logement. |
| `Libelle_designataire_proposition` | `nvarchar(70)` |  | Libellé en clair designataire de la proposition de logement. |
| `Libelle_modification_organisme` | `nvarchar(70)` |  | Libellé en clair de modification organisme. |
| `Indicateur_logement_flux` | `nvarchar(4)` |  | Indicateur (valeur booléenne ou O/N) du logement flux. |
| `Libelle_motif_hors_flux` | `nvarchar(50)` |  | Libellé en clair du motif hors flux. |
| `ID_delagataire_proposition` | `nvarchar(10)` |  | Identifiant unique delagataire de la proposition de logement. |
| `Libelle_delegataire_proposition` | `nvarchar(70)` |  | Libellé en clair délégataire de la proposition de logement. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Reglementation

*Référentiel · 7 colonnes*

Référentiel des obligations et seuils réglementaires applicables au patrimoine.

Jointures : `ID_lot` → `DWH.Lot.ID_lot` (plusieurs vers un)

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_lot` | `varchar(15)` | NN | > Identifiant du lot. |
| `Code_societe` | `varchar(3)` |  | Code de nomenclature de la société. |
| `Code_lot` | `varchar(6)` |  | > Code du lot. |
| `Type_reglementation` | `varchar(15)` |  | > Réglementation à laquelle s'expose le lot. |
| `Eligibilite` | `varchar(3)` |  | Eligibilite. |
| `Etat_conformite_reglementaire` | `varchar(15)` |  | État conformite réglementaire. |
| `Date_actualisation` | `datetime` |  | >  Date d'actualisation des données. |


### DWH_Releve_compte_client_historique

*Bail et locataire · 79 colonnes*

Historisation des releves de compte client, par mois et par catégorie de mouvement.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_client` | `nvarchar(10)` | RGPD | Identifiant unique du client. |
| `ID_client_annee_mois` | `nvarchar(20)` | NN RGPD | Identifiant unique du client de l'annee en mois. |
| `Annee_mois` | `nvarchar(7)` |  | Annee en mois. |
| `Annee_mois_ordre` | `int` |  | Annee en mois de l'ordre. |
| `Code_societe` | `nvarchar(3)` |  | Code de nomenclature de la société. |
| `Code_client` | `nvarchar(6)` | RGPD | Code de nomenclature du client. |
| `Montant_solde_client` | `float(53)` | RGPD | Montant en euros du solde du compte client du client. |
| `Date_ecriture_retenue_solde_client` | `date` | RGPD | Date de l'écriture comptable retenue du solde du compte client du client. |
| `Numero_ecriture_retenue_solde_client` | `int` | RGPD | Numéro de l'écriture comptable retenue du solde du compte client du client. |
| `Montant_impaye_potentiel` | `float(53)` |  | Montant en euros de l'impayé potentiel. |
| `Classe_montant_impaye_potentiel` | `nvarchar(50)` |  | Montant cumulé CA. |
| `Montant_sommes_attente` | `float(53)` |  | Titre du paiement. |
| `Montant_impaye_retardataire` | `float(53)` |  | Montant en euros de l'impayé retardataire. |
| `Montant_impaye` | `float(53)` |  | Montant en euros de l'impayé. |
| `Classe_montant_impaye` | `nvarchar(50)` |  | Titre du paiement. |
| `Indicateur_anciennete_impaye` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) ancienneté de l'impayé. |
| `Indicateur_evolution_impaye` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) evolution de l'impayé. |
| `Evolution_montant_impaye` | `float(53)` |  | Evolution montant impayé : evolution montant de l'impayé. |
| `Montant_categorie_loyer` | `float(53)` |  | Montant en euros de la catégorie du loyer. |
| `Montant_categorie_aide_logement` | `float(53)` |  | Montant en euros de la catégorie de l'aide au logement du logement. |
| `Montant_categorie_provision_charges` | `float(53)` |  | Montant en euros de la catégorie provision des charges locatives. |
| `Montant_categorie_solde_charges` | `float(53)` |  | Montant en euros de la catégorie du solde du compte client des charges locatives. |
| `Montant_categorie_surloyer` | `float(53)` |  | Montant en euros de la catégorie surloyer. |
| `Montant_categorie_penalite_enquete` | `float(53)` |  | Montant en euros de la catégorie penalite de l'enquete. |
| `Montant_categorie_depot_garantie` | `float(53)` |  | Montant en euros de la catégorie du dépôt de garantie de garantie. |
| `Montant_categorie_accession` | `float(53)` |  | Montant en euros de la catégorie de l'accession à la propriété. |
| `Montant_categorie_taxes` | `float(53)` |  | Montant en euros de la catégorie taxes. |
| `Montant_categorie_divers` | `float(53)` |  | Montant en euros de la catégorie divers. |
| `Montant_categorie_facturation_immediate` | `float(53)` |  | Montant écriture CA. |
| `Montant_loyer` | `float(53)` |  | Montant en euros du loyer. |
| `Montant_loyer_residuel_hors_rappel_APL_RLS` | `float(53)` |  | Montant écriture CA. |
| `Indicateur_evolution_loyer_residuel_hors_rappel_APL_RLS` | `nvarchar(10)` |  | Indicateur (valeur booléenne ou O/N) evolution du loyer residuel hors rappel de l'APL (aide personnalisee au… |
| `Evolution_montant_loyer_residuel_hors_rappel_APL_RLS` | `float(53)` |  | Evolution montant loyer residuel hors rappel APL RLS : evolution montant du loyer residuel hors rappel de l'A… |
| `Montant_loyer_residuel_avec_rappel_APL_RLS` | `float(53)` |  | Montant écriture CA. |
| `Montant_APL` | `float(53)` |  | Montant en euros de l'APL (aide personnalisee au logement). |
| `Indicateur_APL` | `nvarchar(50)` |  | Indicateur (valeur booléenne ou O/N) de l'APL (aide personnalisee au logement). |
| `Montant_rappel_APL` | `float(53)` |  | Montant en euros rappel de l'APL (aide personnalisee au logement). |
| `Montant_RLS` | `float(53)` |  | Code rubrique. |
| `Montant_rappel_RLS` | `float(53)` |  | Code rubrique. |
| `Montant_allocation_logement` | `float(53)` |  | Montant en euros allocation du logement. |
| `Montant_charges` | `float(53)` |  | Montant en euros des charges locatives. |
| `Montant_charges_facturation_client` | `float(53)` | RGPD | Montant en euros des charges locatives facturation du client. |
| `Montant_charges_facturation_immediate` | `float(53)` |  | Code opération. |
| `Montant_SLS` | `float(53)` |  | Code rubrique. |
| `Montant_penalite_SLS` | `nvarchar(50)` |  | Code rubrique. |
| `Indicateur_penalite_SLS` | `nvarchar(50)` |  | Code rubrique. |
| `Montant_penalite_assurance` | `float(53)` |  | Code rubrique. |
| `Montant_travaux` | `float(53)` |  | Montant en euros des travaux. |
| `Montant_travaux_depuis_fin_bail` | `float(53)` |  | Montant en euros des travaux depuis le fin du bail. |
| `Montant_travaux_cumule` | `float(53)` |  | Montant en euros des travaux cumule. |
| `Montant_frais_procedure` | `float(53)` |  | Montant en euros frais de la procédure stockée. |
| `Montant_frais_procedure_depuis_dernier_solde_crediteur` | `float(53)` |  | Date opération. |
| `Montant_frais_procedure_cumule` | `float(53)` |  | Date opération. |
| `Indicateur_mandat_prelevement_quittancement` | `nvarchar(50)` |  | Titre du paiement. |
| `Jour_mandat_prelevement_quittancement` | `int` |  | Titre du paiement. |
| `Indicateur_mandat_prelevement_accord_reglement` | `nvarchar(50)` |  | Titre du paiement. |
| `Jour_mandat_prelevement_accord_reglement` | `int` |  | Titre du paiement. |
| `Libelle_type_paiement_majoritaire` | `nvarchar(100)` |  | Montant écriture CA. |
| `Montant_paiement_prelevement` | `float(53)` |  | Montant écriture CA. |
| `Montant_rejet_prelevement` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_virement_bancaire` | `float(53)` |  | Montant écriture CA. |
| `Montant_remboursement_virement_bancaire` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_carte_bancaire` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_cheque` | `float(53)` |  | Montant écriture CA. |
| `Montant_remboursement_cheque` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_espece` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_mandat` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_tpe` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_ecriture_manuelle` | `float(53)` |  | Montant écriture CA. |
| `Montant_paiement_moins_remboursement` | `float(53)` |  | Montant écriture CA. |
| `Montant_total_accords_reglements_actifs` | `float(53)` |  | Montant échéance. |
| `Indicateur_accords_reglements_actifs` | `nvarchar(50)` |  | Montant échéance. |
| `Montant_echeances_passees_accords_reglements_actifs` | `float(53)` |  | Montant échéance. |
| `Montant_echeances_passees_respectees_accords_reglements_actifs` | `float(53)` |  | Ind respect accord. |
| `Montant_echeances_passees_non_respectees_accords_reglements_actifs` | `float(53)` |  | Ind respect accord. |
| `Montant_echeances_en_cours_accords_reglements_actifs` | `float(53)` |  | Montant échéance. |
| `Montant_echeances_a_venir_accords_reglements_actifs` | `float(53)` | RGPD | Montant échéance. |
| `Libelle_activite_echeanciers` | `nvarchar(50)` |  | Libellé en clair de l'activite d'exécution echeanciers. |
| `Date_actualisation` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Utilisateur

*Organisation · 17 colonnes · PK : `ID_utillisateur`*

Utilisateurs des applications du système d'information.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_utillisateur` | `nvarchar(50)` | PK NN | Identifiant unique utillisateur. |
| `Nom_complet_utilisateur` | `nvarchar(255)` | RGPD | Nom complet de l'utilisateur. |
| `Prenom` | `nvarchar(255)` | RGPD | Prenom d'utilisateur. |
| `Nom` | `nvarchar(255)` | RGPD | Nom d'utilisateur. |
| `Adresse_mail` | `nvarchar(255)` | RGPD | Adresse adresse de courriel. |
| `ID_principal` | `nvarchar(255)` |  | Identifiant unique principal. |
| `poste` | `nvarchar(255)` |  | Poste. |
| `service` | `nvarchar(255)` |  | Service : en service. |
| `Societe` | `nvarchar(255)` |  | Société. |
| `Bureau` | `nvarchar(255)` |  | Bureau. |
| `Ville` | `nvarchar(255)` |  | Ville : commune. |
| `Pays` | `nvarchar(255)` |  | Pays. |
| `Matricule` | `nvarchar(50)` |  | Matricule. |
| `Compte_actif` | `bit` |  | Compte actif. |
| `ID_manager` | `nvarchar(50)` | RGPD | Identifiant unique manager. |
| `Nom_manager` | `nvarchar(255)` | RGPD | Nom manager. |
| `Date_maj` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |


### DWH_Utilisateur_hierarchie

*Organisation · 6 colonnes · PK : `ID_utilisateur, ID_manager`*

Hiérarchie des utilisateurs, utilisée pour la sécurité au niveau des lignes.

| Colonne | Type | Clés | Description |
|---|---|---|---|
| `ID_utilisateur` | `nvarchar(50)` | PK NN | Identifiant unique de l'utilisateur. |
| `ID_manager` | `nvarchar(50)` | PK NN RGPD | Identifiant unique manager. |
| `Nom_complet_utilisateur` | `nvarchar(255)` | RGPD | Nom complet de l'utilisateur. |
| `Nom_manager` | `nvarchar(255)` | RGPD | Nom manager. |
| `Niveau` | `int` | NN | Niveau d'utilisateur hiérarchie. |
| `Date_maj` | `datetime` |  | Horodatage de la dernière actualisation de la ligne dans l'entrepôt. Champ technique alimenté automatiquement. |
