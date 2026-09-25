# Dictionnaire de données — bailleur_social.db

Base d'un bailleur social : patrimoine (bâtiments, logements), locataires (clients, occupants, baux), gestion locative (comptes, interventions, troubles) et suivi technique (équipements, diagnostics).

**Convention commune à toutes les tables** : `Date_actualisation` (TEXT, format AAAA-MM-DD) indique la date de dernière mise à jour de la ligne ; elle n'est pas redocumentée table par table. Les indicateurs binaires (`Indicateur_*`) valent 0 ou 1. Les identifiants `ID_*` sont des clés techniques auto-incrémentées.

## Schéma relationnel (clés étrangères)

```
Batiment ──< Logement ──< Bail >── Client ──< Occupant
    │            │                    │
    │            ├──< Diagnostique    ├──< Releve_de_compte_client
    │            ├──< Equipement      ├──< Enquete_satisfaction
    │            ├──< Intervention    └──< Trouble
    │            ├──< Logement_historique
    │            └──< Enquete_satisfaction, Trouble
    └──< Copropriete
```
`<` signifie « plusieurs lignes rattachées à une seule » (ex. plusieurs logements par bâtiment).

---

## Batiment (30 lignes)
Un immeuble du patrimoine du bailleur.

| Colonne | Type | Description |
|---|---|---|
| ID_batiment | INTEGER, clé primaire | Identifiant technique du bâtiment |
| Code_batiment | TEXT | Code métier du bâtiment |
| Nom_batiment | TEXT | Nom usuel du bâtiment |
| Adresse | TEXT | Adresse postale |
| Code_postal | TEXT | Code postal |
| Ville | TEXT | Ville |
| Code_INSEE_commune | TEXT | Code INSEE de la commune |
| Annee_construction | INTEGER | Année de construction |
| Nombre_etages | INTEGER | Nombre d'étages |
| Nombre_logements | INTEGER | Nombre de logements dans le bâtiment |
| Type_chauffage | TEXT | Mode de chauffage. Valeurs : `Collectif gaz`, `Collectif fioul`, `Individuel electrique`, `Reseau de chaleur` |
| Classe_DPE | TEXT | Classe de diagnostic de performance énergétique du bâtiment, de `A` (meilleure) à `G` (pire) |
| Code_societe | TEXT | Société du groupe propriétaire. Valeurs observées : `SOC01`, `SOC02`, `SOC03` |

## Copropriete (10 lignes)
Informations de copropriété pour les bâtiments concernés (un bâtiment n'est pas forcément en copropriété).

| Colonne | Type | Description |
|---|---|---|
| ID_copropriete | INTEGER, clé primaire | Identifiant technique |
| ID_batiment | INTEGER, FK → Batiment | Bâtiment concerné |
| Nom_copropriete | TEXT | Nom de la copropriété |
| ID_immatriculation | TEXT | Numéro d'immatriculation officiel de la copropriété |
| Nom_syndic | TEXT | Nom du syndic de copropriété |
| Adresse_syndic | TEXT | Adresse du syndic |
| Telephone_syndic | TEXT | Téléphone du syndic |
| Mail_syndic | TEXT | E-mail du syndic |
| Date_immatriculation | TEXT (date) | Date d'immatriculation de la copropriété |
| Total_tantiemes | INTEGER | Nombre total de tantièmes de la copropriété |
| Etat_mandat | TEXT | État du mandat du syndic. Valeurs : `Actif`, `En attente AG`, `Renouvele` |
| Date_fin_mandat | TEXT (date) | Date de fin du mandat du syndic |

## Logement (433 lignes)
Un logement individuel, rattaché à un bâtiment.

| Colonne | Type | Description |
|---|---|---|
| ID_logement | INTEGER, clé primaire | Identifiant technique du logement |
| Code_logement | TEXT | Code métier du logement (ex. `LOG00001`) |
| ID_batiment | INTEGER, FK → Batiment | Bâtiment auquel appartient le logement |
| Etage | INTEGER | Étage du logement |
| Numero_porte | TEXT | Numéro de porte |
| Type_logement | TEXT | Typologie. Valeurs : `T1` à `T5` |
| Surface_habitable | REAL | Surface habitable en m² |
| Nombre_pieces | INTEGER | Nombre de pièces |
| Code_categorie_financement | TEXT | Régime de financement du logement social. Valeurs : `PLAI` (loyers les plus bas, publics très modestes), `PLUS` (financement social standard), `PLS` (loyers un peu plus élevés), `Intermediaire` (logement intermédiaire) |
| Code_etat_actuel | TEXT | État locatif actuel. Valeurs : `Libre` (vacant), `Loue`, `Preavis` (locataire partant), `Travaux` |
| Date_mise_en_service | TEXT (date) | Date de mise en service du logement |
| Loyer_reference | REAL | Loyer de référence (hors charges), en euros |
| Indicateur_accessibilite_PMR | INTEGER (0/1) | Logement accessible aux personnes à mobilité réduite |

## Logement_historique (2 598 lignes)
Historique mensuel de l'état et du loyer d'un logement (une ligne par logement et par mois).

| Colonne | Type | Description |
|---|---|---|
| ID_logement_historique | INTEGER, clé primaire | Identifiant technique de la ligne d'historique |
| ID_logement | INTEGER, FK → Logement | Logement concerné |
| Annee_mois | TEXT | Période au format `AAAAMM` (ex. `202510` pour octobre 2025) |
| Code_etat | TEXT | État du logement ce mois-là. Valeurs : `Loue`, `Libre`, `Travaux` |
| Loyer_applique | REAL | Loyer appliqué ce mois-là, en euros |
| Charges_appliquees | REAL | Charges appliquées ce mois-là, en euros |
| Indicateur_vacance | INTEGER (0/1) | Logement vacant (inoccupé) ce mois-là |
| Nombre_jours_vacance | INTEGER | Nombre de jours de vacance dans le mois |

## Client (220 lignes)
Le titulaire du bail (locataire principal). À ne pas confondre avec `Occupant` (les personnes qui vivent avec lui).

| Colonne | Type | Description |
|---|---|---|
| ID_client | INTEGER, clé primaire | Identifiant technique du client |
| Nom_client | TEXT | Nom de famille |
| Prenom_client | TEXT | Prénom |
| Date_naissance | TEXT (date) | Date de naissance |
| Annee_revenus | INTEGER | Année de référence des revenus déclarés |
| Montant_revenus | REAL | Montant des revenus annuels déclarés, en euros |
| Code_categorie_menage | TEXT | Composition du foyer. Valeurs : `Personne seule`, `Couple sans enfant`, `Couple avec enfants`, `Famille monoparentale`, `Colocation` |
| Mail_client | TEXT | Adresse e-mail |
| Telephone_client | TEXT | Numéro de téléphone |
| Adresse_temporaire | TEXT | Adresse temporaire, si le client ne réside pas (encore) dans le logement loué |

## Occupant (171 lignes)
Personne vivant dans le logement en plus (ou à la place) du client titulaire du bail.

| Colonne | Type | Description |
|---|---|---|
| ID_occupant | INTEGER, clé primaire | Identifiant technique |
| ID_client | INTEGER, FK → Client | Client (bail) auquel l'occupant est rattaché |
| Nom_occupant | TEXT | Nom de famille de l'occupant |
| Prenom_occupant | TEXT | Prénom de l'occupant |
| Date_naissance | TEXT (date) | Date de naissance de l'occupant |
| Lien_parente | TEXT | Lien avec le client titulaire. Valeurs : `Conjoint`, `Enfant`, `Autre` |
| Date_entree | TEXT (date) | Date d'entrée de l'occupant dans le logement |

## Bail (220 lignes)
Le contrat de location liant un client à un logement.

| Colonne | Type | Description |
|---|---|---|
| ID_bail | INTEGER, clé primaire | Identifiant technique du bail |
| ID_client | INTEGER, FK → Client | Locataire titulaire |
| ID_logement | INTEGER, FK → Logement | Logement loué |
| Type_bail | TEXT | Nature du bail. Valeurs : `Bail principal`, `Bail glissant` (transitoire, souvent via une association), `Sous-location autorisee` |
| Date_debut_occupation | TEXT (date) | Date de début d'occupation |
| Date_fin_occupation | TEXT (date), peut être vide | Date de fin d'occupation (vide si le bail est en cours) |
| Montant_loyer | REAL | Loyer mensuel du bail, en euros |
| Montant_charges | REAL | Charges mensuelles du bail, en euros |
| Date_reception_preavis | TEXT (date), peut être vide | Date de réception du préavis de départ, si donné |
| Statut_bail | TEXT | Statut. Valeurs : `En cours`, `Termine` |

## Releve_de_compte_client (2 640 lignes)
Situation comptable mensuelle d'un client (loyer dû, aides, paiements, impayés).

| Colonne | Type | Description |
|---|---|---|
| ID_releve | INTEGER, clé primaire | Identifiant technique |
| ID_client | INTEGER, FK → Client | Client concerné |
| Annee_mois | TEXT | Période au format `AAAAMM` |
| Montant_loyer | REAL | Loyer dû ce mois-là, en euros |
| Montant_charges | REAL | Charges dues ce mois-là, en euros |
| Montant_APL | REAL | Aide personnalisée au logement déduite, en euros |
| Montant_paye | REAL | Montant effectivement payé par le client, en euros |
| Montant_impaye | REAL | Montant restant impayé sur la période, en euros |
| Classe_montant_impaye | TEXT | Niveau d'impayé. Valeurs : `Aucun`, `Faible`, `Eleve` |
| Solde_client | REAL | Solde du compte client (négatif = le bailleur doit de l'argent au client ; positif = le client doit de l'argent) |

## Equipement (1 295 lignes)
Un équipement technique installé dans un logement.

| Colonne | Type | Description |
|---|---|---|
| ID_equipement | INTEGER, clé primaire | Identifiant technique |
| ID_logement | INTEGER, FK → Logement | Logement équipé |
| Code_famille_equipement | TEXT | Famille de l'équipement. Valeurs : `Chauffage`, `Cuisine`, `Sanitaire`, `Ventilation`, `Ouvrants` |
| Code_type_equipement | TEXT | Type précis. Ex. `Chaudiere`, `PAC`, `Radiateur electrique`, `Plaque de cuisson`, `Hotte`, `Robinetterie`, `VMC simple flux`, `VMC double flux`, `Fenetre PVC`, `Volet roulant`, `Chauffe-eau` |
| Marque | TEXT | Marque de l'équipement |
| Modele | TEXT | Modèle de l'équipement |
| Date_installation | TEXT (date) | Date d'installation |
| Date_fin_de_service | TEXT (date), peut être vide | Date de fin de service (vide si toujours en service) |
| Etat_equipement | TEXT | État. Valeurs : `Bon`, `Moyen`, `A remplacer` |

## Diagnostique (643 lignes)
Un diagnostic technique ou réglementaire réalisé sur un logement.

| Colonne | Type | Description |
|---|---|---|
| ID_diagnostic | INTEGER, clé primaire | Identifiant technique |
| ID_logement | INTEGER, FK → Logement | Logement concerné |
| Type_diagnostic | TEXT | Nature du diagnostic. Valeurs : `DPE`, `Gaz`, `Electricite`, `Plomb`, `Amiante`, `Termites` |
| Date_debut_diagnostic | TEXT (date) | Date de réalisation du diagnostic |
| Date_fin_diagnostic | TEXT (date) | Date de fin de validité du diagnostic |
| Resultat_diagnostic | TEXT | Résultat. Valeurs : `Conforme`, `A surveiller`, `Non conforme` |
| Indicateur_perime | INTEGER (0/1) | Le diagnostic a dépassé sa date de fin de validité |
| Nombre_jours_avant_peremption | INTEGER | Nombre de jours restants avant péremption (négatif si déjà périmé) |

## Intervention (500 lignes)
Une intervention technique (maintenance, réparation) réalisée ou planifiée sur un logement.

| Colonne | Type | Description |
|---|---|---|
| ID_intervention | INTEGER, clé primaire | Identifiant technique |
| ID_logement | INTEGER, FK → Logement | Logement concerné |
| Type_intervention | TEXT | Corps de métier. Valeurs : `Plomberie`, `Electricite`, `Chauffage`, `Serrurerie`, `Peinture`, `Espaces verts`, `Menage parties communes` |
| Libelle_intervention | TEXT | Libellé libre décrivant l'intervention |
| Prestataire | TEXT | Nom du prestataire intervenant |
| Date_enregistrement | TEXT (date) | Date d'enregistrement de la demande |
| Date_realisation | TEXT (date), peut être vide | Date de réalisation effective (vide si non encore réalisée) |
| Montant_HT | REAL | Montant hors taxes, en euros |
| Montant_TTC | REAL | Montant toutes taxes comprises, en euros |
| Statut_intervention | TEXT | Statut. Valeurs : `Planifiee`, `En cours`, `Realisee`, `Annulee` |

## Trouble (140 lignes)
Un trouble de voisinage ou un manquement signalé, lié à un logement et à un client.

| Colonne | Type | Description |
|---|---|---|
| ID_trouble | INTEGER, clé primaire | Identifiant technique |
| ID_logement | INTEGER, FK → Logement | Logement concerné |
| ID_client | INTEGER, FK → Client | Client mis en cause ou concerné |
| Type_trouble | TEXT | Nature du trouble. Valeurs : `Nuisance sonore`, `Conflit voisinage`, `Degradation`, `Depot sauvage`, `Animaux non declares`, `Sous-location illegale` |
| Date_signalement | TEXT (date) | Date de signalement |
| Date_resolution | TEXT (date), peut être vide | Date de résolution (vide si non résolu) |
| Statut_trouble | TEXT | Statut. Valeurs : `En attente`, `En cours`, `Resolu` |
| Description | TEXT | Description libre du trouble |

## Enquete_satisfaction (160 lignes)
Réponse d'un client à une enquête de satisfaction, liée à un logement.

| Colonne | Type | Description |
|---|---|---|
| ID_enquete | INTEGER, clé primaire | Identifiant technique |
| ID_client | INTEGER, FK → Client | Client interrogé |
| ID_logement | INTEGER, FK → Logement | Logement concerné |
| Date_enquete | TEXT (date) | Date de l'enquête |
| Note_globale | INTEGER (1 à 5) | Note de satisfaction globale |
| Note_logement | INTEGER (1 à 5) | Note de satisfaction sur le logement |
| Note_proprete_parties_communes | INTEGER (1 à 5) | Note de satisfaction sur la propreté des parties communes |
| Note_reactivite_service | INTEGER (1 à 5) | Note de satisfaction sur la réactivité des services |
| Indicateur_recommandation | INTEGER (0/1) | Le client recommanderait le bailleur |
| Commentaire | TEXT | Commentaire libre du client |

---

## Notes pour l'assistant IA (génération de requêtes)

- **Locataire vs occupant** : `Client` = titulaire du bail (paie le loyer). `Occupant` = personnes du foyer non titulaires (conjoint, enfants…). Pour « qui habite le logement », penser aux deux tables.
- **Logement vacant** : `Logement.Code_etat_actuel = 'Libre'` pour l'état courant, ou `Logement_historique.Indicateur_vacance = 1` pour un mois donné.
- **Impayés** : `Releve_de_compte_client.Montant_impaye` (montant) ou `Classe_montant_impaye` (catégorie `Aucun`/`Faible`/`Eleve`). `Solde_client` négatif = en faveur du client.
- **Logement social par niveau de loyer** : du plus social au moins social, `PLAI` < `PLUS` < `PLS` < `Intermediaire` (colonne `Code_categorie_financement`).
- **Diagnostic à renouveler** : `Diagnostique.Indicateur_perime = 1` ou `Nombre_jours_avant_peremption < 0` (ou proche de 0 pour anticiper).
- **Périodes** : `Annee_mois` (dans `Logement_historique` et `Releve_de_compte_client`) est au format `AAAAMM` (texte), pas une vraie date — pas de fonctions `date()` SQLite dessus directement.
