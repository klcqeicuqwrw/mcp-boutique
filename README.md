# 🤖 Assistant IA de Base de Données (Langage Naturel vers SQL)

Ce projet est une application web complète permettant d'interroger une base de données relationnelle (SQLite) en **langage naturel** grâce à l'intelligence artificielle (Google Gemini). L'application traduit les questions des utilisateurs en requêtes SQL, les exécute de manière hautement sécurisée, et restitue les résultats sous forme de tableaux, de graphiques ou de synthèses textuelles.

Il est conçu pour s'adapter à n'importe quel contexte métier (ex: gestion de boutique, bailleur social) en limitant strictement l'accès aux données selon le profil de l'utilisateur.

---

## ⚙️ Comment ça fonctionne (Étape par Étape)

1. **🔐 Authentification et Autorisation :** L'utilisateur se connecte via l'interface web. Le système identifie son rôle (ex: RH, Finance, Admin) et déduit quelles tables et colonnes de la base de données il a le droit de consulter.
2. **🧹 Filtrage du Schéma :** Le système extrait la structure de la base de données (le "schéma") mais en retire dynamiquement toutes les informations interdites pour cet utilisateur.
3. **🧠 Traduction par l'IA (Gemini) :** L'application envoie à Gemini le schéma filtré, le dictionnaire de règles métier, l'historique de la conversation et la question de l'utilisateur. Gemini renvoie une requête SQL pure.
4. **🛡️ Validation de Sécurité :** Le système vérifie que la requête générée est strictement une opération de lecture (`SELECT`, `WITH`) et interdit toute modification (`INSERT`, `DROP`, `UPDATE`).
5. **⚡ Exécution Restreinte :** La requête est exécutée sur la base SQLite connectée en mode "Lecture Seule" (`?mode=ro`). Un filtre SQLite (`authorizer`) bloque l'exécution en temps réel si l'IA tente de contourner les droits (via des sous-requêtes, par exemple).
6. **📊 Restitution des Données :** Les résultats sont formatés. Si demandé, l'IA génère une courte phrase de synthèse. Si la question implique une visualisation, l'IA détermine le meilleur graphique (camembert, barres) pour représenter les données. Les résultats sont affichés à l'utilisateur, qui peut ensuite les exporter (CSV, PDF, Excel).

---

## 📁 Architecture du Projet (Rôle des Fichiers et Dossiers)

### 🐍 Les Fichiers Python (Backend)

* **`main.py`** *(Le Chef d'Orchestre)* : C'est le point d'entrée principal du serveur web en production. Il gère le routage des pages web, l'authentification (sessions par cookies), les exports de données (PDF, Excel, CSV), la génération dynamique des graphiques, et expose les routes du panneau d'administration.
* **`api.py`** *(Le Moteur IA)* : Contient la logique de communication avec Google Gemini. Il centralise la création des "prompts" (les instructions envoyées à l'IA) pour traduire le français en SQL, et pour résumer les résultats textuellement. Il gère également les tentatives de reconnexion en cas de surcharge de l'API Google.
* **`securite.py`** *(Le Gardien)* : Gère l'intégralité de la sécurité de l'application. Il contient la gestion de la base de données interne `app.db` (utilisateurs, mots de passe, logs), le système de filtrage d'accès (qui a le droit de voir quelle table/colonne), et les fonctions d'audit (journalisation de toutes les requêtes SQL exécutées et des tokens IA consommés).
* **`server.py`** *(L'Interface MCP)* : Un script indépendant qui permet de transformer l'application en un serveur "MCP" (Model Context Protocol). Cela permet de connecter directement votre base de données locale à des assistants IA de bureau (comme Claude Desktop ou Github Copilot), pour qu'ils puissent interroger la base sans passer par l'interface web.

### 📂 Les Dossiers et Fichiers Annexes

* **`web/`** *(Le Frontend)* : Ce dossier contient tous les fichiers statiques de l'interface utilisateur.
* `index.html` : L'interface de chat pour poser les questions.
* `admin.html` : Le tableau de bord pour gérer les utilisateurs, leurs permissions et consulter les logs.
* `login.html` / `reset.html` : Les pages de connexion et de mot de passe oublié.
* `static/` : Sous-dossier contenant le CSS, les images et le JavaScript.


* **`.env`** : Le fichier de configuration de l'environnement. Il contient les informations sensibles qui ne doivent jamais être dans le code source (clé API Gemini, chemins vers les bases de données, mot de passe admin par défaut).
* **`dictionnaire_donnees_*.md`** : Un fichier texte essentiel agissant comme le "cerveau métier" de l'IA. Il explique à Gemini le sens des données (ex: *"La colonne Code_etat à Libre signifie que le logement est vide"*).
* **Bases de données (`.db`)** :
* `app.db` : Créée automatiquement par le système, elle stocke les utilisateurs, les droits et l'historique des chats.
* `votre_base_metier.db` : Votre propre base de données SQLite contenant les vraies informations à interroger.


Pour lancer le website : http://127.0.0.1:8000

Liste des tables : 
    - clients
    - fournisseurs
    - produits
    - employes
    - commandes
    - lignes_commande

Texte terminal = 
    git add .
    git commit -m "Votre message de commit"
    git push