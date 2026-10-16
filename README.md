# Assistant de données métier — mcp-boutique

Le bouton **Prévisions** ouvre deux prototypes ML locaux. Les modèles sont
implémentés en Python standard (`boutique/apprentissage.py`) pour fonctionner
sans bibliothèques natives sur les postes soumis au contrôle d'applications Windows.
Ils n'utilisent aucune API payante et ne modifient pas la BDD métier.

Le jeu fictif a été enrichi par `scripts/enrichir_historiques_predictions.py` :
21 mois complets (janvier 2025–septembre 2026) pour 320 comptes clients, et trois
ans de suivi simulé (octobre 2023–septembre 2026, à partir de la mise en service)
pour 615 équipements. Les 871 pannes générées portent un `ID_equipement` explicite
dans `Intervention`, `Indicateur_panne='Oui'` et `Origine_donnees`. Le suivi continu
déclaré dans `Equipement` porte `Date_debut_observation`, `Date_fin_observation`
et `Origine_observation`. Ces valeurs décrivent une simulation complète, jamais
une collecte réelle. Les anciennes lignes restent inchangées ; la provenance et
la graine sont conservées dans `Simulation_dataset`. Le générateur sauvegarde le
DWH et le dictionnaire, travaille en transaction et peut être relancé sans doublon.
Les mesures de performance sur ce jeu synthétique ne valident pas le modèle sur
des situations réelles ; elles peuvent refléter les règles du générateur.

- **Impayés** : régression Ridge (pénalité L2 = 10) sur l'évolution entre deux mois
  consécutifs. Les variables financières accessibles au service sont imputées par
  la médiane et standardisées sur le seul jeu d'apprentissage. La sortie est une
  somme agrégée, jamais un score de client. La cohorte est fixe entre les mois
  comparés ; un mois couvrant moins de 95 % du maximum de clients observés est
  exclu du graphique comparable. Ce seuil ne garantit pas une complétude métier.
  Le modèle prévoit uniquement le mois suivant les dernières données comparables,
  sans extrapoler un historique ancien jusqu'au mois actuel. Un test chronologique
  compare l'erreur moyenne à la référence « impayé inchangé » quand les données le
  permettent. Aucun intervalle de confiance calibré n'est annoncé.
- **Équipements** : régression logistique L2 sur des fenêtres non chevauchantes de
  90 jours. Les pannes datées explicitement liées à l'équipement sont prioritaires
  lorsque leurs colonnes et celles de la couverture du suivi sont accessibles.
  Chaque fenêtre d'entraînement doit être intégralement couverte pour cet
  équipement ; le score est calculé au dernier jour observé, sans inventer des
  jours sans panne après ce jour. Sans ces champs, un mode indirect reste disponible : une commande mentionne une panne/HS et le
  code d'intervention, l'objet et le type d'équipement doivent être cohérents. Le
  rapprochement lot/type doit désigner un seul équipement déjà en service.
  Contrôles sans panne, ambiguïtés et identifiants contradictoires sont exclus.
  Seuls les types ayant au moins 10 signaux avant la période de test sont retenus.
  Variables : âge, signaux antérieurs sur 90/365 jours, délai depuis le dernier
  signal et type. La sortie est un **indice relatif de priorité de contrôle**, pas
  une probabilité de panne physique : les scores du modèle sont classés entre les
  équipements éligibles, en tenant compte des ex æquo. Le modèle n'est pas calibré.
  L'AUC n'est affichée que si la période test contient au moins cinq positifs et
  les deux classes ; sinon la qualité prédictive reste explicitement non établie.
  En mode direct simulé, l'AUC est présentée comme une mesure sur des pannes
  synthétiques, jamais comme une preuve de fiabilité sur des équipements réels.
  Les types non couverts sont indiqués comme non estimables. Pour une vraie
  estimation du risque, il faut un journal de pannes daté lié à `ID_equipement`,
  une couverture d'observation vérifiée et des données réelles suffisantes.

Les prédictions respectent les permissions de tables et de colonnes, vérifiées
avant l'extraction et à nouveau avant de renvoyer le résultat. Les modèles sont
réentraînés en mémoire à chaque consultation. Une extraction tronquée est refusée,
et les observations équipement/période sont limitées à 20 000 pour ce prototype.
La base actuelle est fictive : les résultats servent à la démonstration et à la
validation technique. Tests : `python -m pytest test_predictions.py -q`.

Le chat propose un espace collaborateur : **À traiter** regroupe les affaires en
retard, commandes à relancer, diagnostics à renouveler, préavis, mandats de syndic
et comptes à examiner. La date de référence est modifiable ; les dates des données
sont affichées. Les calculs sont locaux, sans appel à une IA. Le suivi des impayés
retient le dernier mois disponible de chaque client à la date choisie.

Dans les tableaux, les identifiants disponibles ouvrent les fiches client,
logement, résidence, affaire, commande, diagnostic, occupant et copropriété dans
un panneau. Les rubriques liées, documents et contacts dépendent des droits du
service. Les fiches client regroupent baux, occupants, logements, affaires,
historiques de compte et procédures ; une courbe peut afficher l'évolution du
compte (Chart.js, avec le tableau conservé en cas d'indisponibilité).

Les boutons IKOS/GED utilisent les liens de la base : les adresses fictives ne
garantissent pas l'accès à un outil réel. **Voir sur la carte** ouvre la page `/carte`
de l'application, filtrée sur les résidences liées à la fiche. Leaflet affiche les
points sur un fond OpenStreetMap ; les droits sont revérifiés par `/api/carte`.
Les anciens liens d'itinéraire redirigent également vers cette carte. Les relances prestataire
et contacts collègues préparent un brouillon à relire et envoyer dans sa messagerie.
**Enregistrer la recherche** sauvegarde la question dans les favoris personnels,
accessibles par **Mes recherches**. Relancer un favori applique les droits actuels
et le fournisseur sélectionné ; aucun résultat métier n'est conservé dans le favori.

Après une mise à jour du code Python, relancer le serveur pour enregistrer les
nouvelles routes et migrer automatiquement la base applicative (table des favoris).
Tests dédiés : `python -m pytest test_espace.py -q`.

Application FastAPI pour interroger une base SQLite en français avec Gemini,
ou Groq, au choix dans le chat.
Elle propose un chat, des tableaux, graphiques, exports, une carte du patrimoine
et une administration des utilisateurs et des permissions. Un serveur MCP local
permet également de consulter la base depuis un assistant compatible.

## Installation sous Windows / PowerShell

Python 3.12 ou supérieur est requis. Depuis le dossier du projet :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-web.txt
Copy-Item .env.example .env
```

Renseigner `GEMINI_API_KEY` dans `.env`, choisir `GEMINI_MODEL` selon les modèles
accessibles à votre compte et définir `ADMIN_PASSWORD` (10 caractères minimum).
Si aucun mot de passe n'est fourni, un mot de passe initial aléatoire est affiché
une seule fois dans le terminal lors de la création du premier administrateur.
La clé Gemini n'est nécessaire qu'au premier appel IA ; les pages et les tests
peuvent démarrer sans clé.

Les comptages simples et autonomes (« Combien de clients distincts y a-t-il ? »,
« Nombre total de lots ») sont exécutés directement en SQL, avec les mêmes droits.
Les listes et chiffres reçoivent une phrase de présentation locale ; le choix
des graphiques est également local. Les demandes explicites d'analyse,
d'explication ou de comparaison conservent la synthèse du fournisseur choisi. Les questions
filtrées et les suites de conversation conservent la génération SQL par le fournisseur choisi.
Cela réduit les appels réseau et l'exposition aux ralentissements du fournisseur.

La base fictive `DWH_fictive_10000_lignes.sqlite` et son dictionnaire
`Dictionnaire_donnees_DWH_fictive_SQLite.md` doivent être présents à la racine.
Les chemins personnalisés se configurent dans `.env`. Lancer les commandes
depuis la racine ; les chemins relatifs des bases sont résolus depuis la racine du projet.

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Ouvrir http://127.0.0.1:8000, puis créer les utilisateurs et attribuer les droits
par service depuis l'administration. Un utilisateur sans service ou sans droits
ne peut consulter aucune table. `/health` expose seulement l'état HTTP.
`main:app` est l'unique application web ; `api.py` contient uniquement le moteur IA.

## Configuration

Voir `.env.example` pour les noms des variables, sans secrets. Ne jamais publier
`.env`, `app.db` ni les bases métier contenant des données réelles.

Le chat propose Gemini / Groq et conserve le choix dans le navigateur.
Chaque demande utilise uniquement le fournisseur choisi, y compris pour la
synthese d'analyse. Aucun secours automatique n'est effectue. Les permissions
et la validation SQL restent appliquees avec tous les fournisseurs.

Configurer `GROQ_API_KEY` dans `.env` pour Groq. `GROQ_MODEL` vaut
`openai/gpt-oss-20b` et `GROQ_TIMEOUT_SECONDS` vaut 30 secondes par defaut.
Le client utilise l'endpoint Groq `https://api.groq.com/openai/v1`, via le SDK
OpenAI deja installe, et Chat Completions avec sortie JSON validee localement.
Une cle Groq ne doit pas etre placee dans `OPENAI_API_KEY`.
Les anciennes preferences OpenAI du navigateur selectionnent maintenant Groq.
L'API conserve le fournisseur `openai` pour compatibilite avec les anciens
resultats, avec une vraie cle `OPENAI_API_KEY` et `OPENAI_MODEL`.
Les journaux IA (`gemini_log`) distinguent les appels avec le prefixe `groq/`.

Seuls les schémas et historiques autorisés sont transmis au fournisseur choisi.

- `SQLITE_DB_PATH` : base métier, ouverte exclusivement en lecture seule.
- `DICTIONNAIRE_PATH` : définitions métier et classification des colonnes sensibles.
- `APP_DB_PATH` : comptes, sessions, conversations et journaux, créés au démarrage.
- `APP_BASE_URL` : URL utilisée dans les e-mails de réinitialisation.
- `COOKIE_SECURE=1` : à activer lorsque le site est servi derrière HTTPS.
- `SMTP_*` : envoi des e-mails ; sans `SMTP_HOST`, les messages sont affichés localement dans le terminal.

Les exports CSV, TSV, JSON, Markdown, PDF et Excel sont disponibles ;
`reportlab` et `openpyxl` font partie des dépendances web.

## Droits et conservation des résultats

Chaque requête SQL est vérifiée puis exécutée avec un authorizer SQLite : les
restrictions s'appliquent aussi aux filtres, tris et sous-requêtes. Le temps SQL
est limité à 12 secondes et les réponses du chat à 500 lignes. Une limite sur la
taille des valeurs et du SQL protège également l'exécution web.

Chaque nouveau message conserve une empreinte de la base configurée, du rôle,
du service et des permissions utilisés pour le produire. Si ces paramètres ne
correspondent plus aux droits actuels, le texte, le SQL et le tableau sont masqués,
l'export et la synthèse sont refusés et le message est exclu du contexte Gemini.
Les questions et conversations restent conservées. Retrouver exactement le même
périmètre de droits rend ces résultats de nouveau accessibles.

Au prochain démarrage, la migration ajoute `messages.access_scope` sans supprimer
de données. Les anciens messages sans empreinte restent consultables : un
administrateur peut consulter ses archives, même si l'ancien schéma a changé.
Pour les autres utilisateurs, le SQL archivé est compilé sans exécution avec les
permissions actuelles avant d'autoriser les réponses et exports. L'appartenance
de chaque conversation à l'utilisateur connecté est toujours vérifiée.
Un résultat JSON endommagé est signalé individuellement sans bloquer l'historique.
Sauvegarder `app.db` avec les outils SQLite habituels avant une mise à jour en production.

Le schéma et le dictionnaire envoyés à Gemini sont filtrés par table et colonne.
Le contexte métier est plafonné à 18 000 caractères et conserve les grains et
jointures documentés dont les colonnes sont autorisées. Les exemples personnels
ne sont pas copiés depuis le dictionnaire. La synthèse reçoit le SQL exécuté et
au plus 20 lignes ; un résultat tronqué indique explicitement que son total est
inconnu. Les données consultables par l'utilisateur peuvent être envoyées à Gemini
pour la synthèse et le choix de graphique ; les prompts et réponses sont journalisés
dans `app.db`, accessible aux administrateurs. Adapter leur durée de conservation
et les droits sur ce fichier aux besoins du déploiement.

## Serveur MCP

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-mcp.txt
.\.venv\Scripts\python.exe server.py
```

Transport `stdio` par défaut. `MCP_TABLES_AUTORISEES` limite les tables accessibles,
`MCP_BLOQUER_RGPD=1` bloque les colonnes classées personnelles, y compris dans les
jointures et filtres. Le serveur accepte les anciens dictionnaires en tableaux
Markdown (`### Table`) et les fiches DWH (`## Table`, listes de colonnes).
Dans les fiches DWH, une ligne `Confidentialité : RGPD` classe explicitement une
colonne. Dans les tableaux, utiliser `RGPD` dans la colonne `Clés`.

Le démarrage est refusé si le blocage est actif sans dictionnaire exploitable ou
sans aucune colonne marquée. Les écarts avec le schéma sont signalés. Mettre à
jour la classification à chaque changement de base ; il ne s'agit pas d'une
détection automatique de toutes les données personnelles. Cette classification
MCP est distincte des permissions web, définies dans l'administration.
Le transport MCP HTTP ne gère pas les comptes web : l'écoute est désormais
limitée aux adresses de boucle locale (`127.0.0.1`, `::1`, `localhost`). Une
adresse réseau, un transport inconnu ou un port invalide provoquent un refus
explicite au démarrage. Une table autorisée inexistante est également refusée.

La configuration VS Code `.vscode/mcp.json` active le blocage RGPD et impose
`stdio`. Pour une démonstration avec les seules données fictives, une valeur
explicite `MCP_BLOQUER_RGPD=0` peut toujours désactiver ce blocage. Une faute
de saisie dans cette variable conserve la protection par défaut. Lorsque le
blocage est actif, les tables et colonnes absentes du dictionnaire sont aussi
interdites ; si le dictionnaire disparaît pendant une session, les lectures
sont refusées. Les aperçus excluent ces colonnes et la recherche de colonnes
consulte le schéma réel pour éviter de proposer des colonnes supprimées.

Protections de ressources du serveur MCP :

- `MCP_MAX_CONCURRENT=4` : au plus quatre outils s'exécutent à la fois (maximum
  configurable : 16). Les appels supplémentaires reçoivent « Serveur occupé ».
  Annuler un appel signale son arrêt au traitement SQLite ; la place reste
  occupée jusqu'à la fin effective du travail.
- `MCP_SQL_TIMEOUT=20` : délai SQL, plafonné à 120 secondes, y compris pour
  le comptage d'une description de table. L'annulation et le délai sont vérifiés
  par le gestionnaire de progression SQLite.
- `MCP_MAX_SQL_CHARS=100000` : longueur SQL maximale en **octets UTF-8**,
  plafonnée à 100 000 ; SQLite limite aussi colonnes, profondeur d'expressions
  et requêtes composées.
- `MCP_MAX_ROWS=500` et `MCP_MAX_CHARS=60000` : lecture progressive des résultats,
  sans charger toutes les lignes avant de limiter la réponse. JSON et Markdown
  respectent la limite de caractères ; une ligne trop grande est refusée avec
  une aide pour réduire sa taille. Les descriptions trop longues sont refusées
  plutôt que coupées en plein JSON. La troncature porte sur des lignes entières.
- Les alias SQL répétés sont renommés sans perdre les valeurs, même si une
  colonne porte déjà un nom comme `a_2`.

Ces limites réduisent les risques de surcharge ; elles ne constituent pas
un quota mémoire du processus ni une isolation système. Une fonction SQLite
coûteuse peut ne vérifier l'annulation qu'au prochain rappel de progression.
Les droits MCP restent distincts des permissions par collaborateur du site.
Une mise à disposition distante nécessiterait une authentification et des
droits adaptés, qui ne sont pas implémentés ici.

Vérification : `python -m pytest test_server.py -q`. Les tests couvrent notamment
une vraie session MCP `stdio` (initialisation, découverte des six outils,
lecture, refus RGPD/écriture et poursuite de la session après erreur), la
surcharge, l'annulation, les alias et les tailles de réponse. Après une mise à
jour, redémarrer `bailleur-social` depuis `MCP: List Servers` dans VS Code.

## Tests et évaluation métier

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Les tests automatisés utilisent des bases temporaires et Gemini simulé. Ils
couvrent SQL et MCP, connexion et CSRF, isolation des conversations, révocation
des droits, exports, migration, carte, dictionnaire réel et agrégats de référence.
Le contrôle du dictionnaire utilise la base fictive du dépôt en lecture seule.
Ces tests ne mesurent pas la qualité réelle du modèle Gemini.

Pour mesurer celle-ci sur quatre questions métier à résultat connu :

```powershell
.\.venv\Scripts\python.exe eval_gemini.py
```

Cette commande facultative consomme quatre appels Gemini avec votre clé et
compare les agrégats générés aux requêtes de référence sur la base configurée.
Elle produit une ligne JSON par question et retourne un code non nul en cas
d'erreur. Elle est prévue pour le schéma DWH fourni et n'est pas lancée par pytest.

## Organisation du code

- `main.py` : assemblage FastAPI et initialisation de la base applicative.
- `boutique/dependencies.py` : contrôles de session, CSRF et rôle administrateur.
- `boutique/auth.py`, `chat.py`, `exports.py`, `admin.py`, `pages.py` : routes par fonction.
- `boutique/graphiques.py` : sélection des graphiques.
- `api.py` : clients Gemini/Groq/OpenAI, génération SQL et synthèse.
- `dictionnaire.py` : parsing partagé et construction du contexte métier filtré.
- `securite.py` : comptes, sessions, droits, exécution SQL et journaux.
- `server.py` : outils MCP et protections propres à ce transport.
- `web/` : interface HTML/CSS/JavaScript.

## Carte et contacts

La carte est proposée uniquement lorsqu’une localisation est demandée dans le
chat (par exemple « Localise ces résultats » ou « Affiche les logements sur une
carte »). Une demande portant sur les derniers résultats réutilise la sélection
sans nouvel appel IA. Les identifiants de patrimoine, lot, client ou occupant
permettent de retrouver les sites, avec contrôle des permissions et de la
propriété de la conversation. Les coordonnées de la base fictive sont réparties
approximativement dans les communes ; elles ne représentent pas les adresses
exactes des résidences. Une sauvegarde précède leur mise à jour.

Les boutons E-mail et SMS préparent un brouillon modifiable, puis ouvrent la
messagerie du collaborateur. Le bouton Appeler ouvre son gestionnaire d’appels.
Aucun message n’est envoyé automatiquement.
