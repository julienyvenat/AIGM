# Documentation et Contexte pour l'Agent de Codage (Jules)
**Projet :** RPG AI Game Master (Application VTT & Studio de Création Multi-Univers)
## 1. Vision Globale du Projet
L'objectif est de créer une plateforme web complète permettant à des joueurs de jouer à un jeu de rôle sur table (TTRPG) où le Maître du Jeu (MJ) est incarné par un système d'IA multi-agents. L'application intègre un **Studio de création de mondes**, un gestionnaire de parties (VTT) avec **Battlemap dynamique**, l'audio en temps réel, et une séparation stricte entre la narration et la mécanique de jeu.
## 2. Stack Technique Requise
 * **Backend :** Python 3.10+, FastAPI (API REST et WebSockets), SQLModel / SQLAlchemy 2.0.
 * **Protocole IA :** Model Context Protocol (MCP) pour la communication entre l'IA et la logique du jeu.
 * **Frontend :** React (Vite), React Router DOM, Tailwind CSS, WebSockets natifs.
 * **Base de données :**
   * SQL (SQLite pour le PoC/Dev) : Pour les personnages, les univers, les entités du lore.
   * Vector DB (ChromaDB) : Pour le RAG (Retrieval-Augmented Generation) et la mémoire.
## 3. L'Architecture Multi-Agents & MCP (Le Cerveau)
Le backend utilise le standard MCP. L'architecture est la suivante :
 1. **L'Agent Narrateur (Le MJ) :** Modèle de langage principal. Décrit l'action, interroge MCP.
 2. **L'Agent Arbitre :** Gère la mécanique, lance les dés, vérifie les règles via le Moteur de Jeu.
 3. **L'Agent Architecte (World Builder) :** Génère les univers (Lore, Factions, PNJ, Lieux) et les formate en JSON strict pour la base de données.
 4. **Le Routeur d'Intentions :** Analyse la phrase du joueur pour déterminer s'il s'agit de RP, d'une commande système (/battle), ou d'une action mécanique.
## 4. RÈGLES D'OR DE L'ARCHITECTURE (CRITIQUE)
 * **Règle n°1 : Le Backend est la seule source de vérité.**
   L'IA ne calcule jamais les PV ou les jets de dés. Le Frontend ne fait que de l'affichage. Avant d'envoyer les statistiques au Frontend via le message WS STATS_UPDATE, le backend doit parser proprement le JSON (listes, inventaire). L'état global du Frontend (App.tsx) est écrasé et remplacé par ce message.
 * **Règle n°2 : Isolation stricte des Univers (Multi-Tenant).**
   Toutes les tables (PNJ, Lieux, Factions, Personnages, Sessions) possèdent une clé étrangère universe_id. Lors d'une requête RAG dans ChromaDB, **le contexte doit obligatoirement être filtré par universe_id dans les métadonnées** pour éviter les fuites de lore entre les parties.
 * **Règle n°3 : L'Event Loop ne doit jamais bloquer.**
   Toute opération synchrone lourde (comme la génération d'images avec DALL-E/Gemini ou les I/O de fichiers) DOIT être enveloppée dans asyncio.to_thread() pour ne pas faire geler (freeze) le serveur WebSocket des autres joueurs.
 * **Règle n°4 : Optimisation BDD (Batch & Context).**
   Les insertions de Lore générées par l'Architecte doivent utiliser session.add_all() et l'API de batch de ChromaDB pour éviter de bloquer la DB. La transaction SQL ne s'ouvre qu'à la toute fin.
## 5. Fonctionnalités Clés & Implémentation
 * **Le Mode Battlemap (VTT) :**
   * Le déclenchement se fait via les commandes de chat /battle et /endbattle.
   * En mode BATTLE, le prompt système du Narrateur devient purement tactique.
   * **RAG Spatial :** Pour éviter d'exploser le contexte LLM, seuls les PNJ ayant le flag is_in_combat = True sont envoyés à l'IA avec leurs coordonnées X et Y.
   * **Frontend :** L'image "top-down" générée par l'IA est affichée en fond. Le quadrillage et les "tokens" (pions) sont gérés par-dessus en CSS pur selon les X,Y reçus du backend.
 * **L'Interface Utilisateur (UI) :**
   * Architecture via react-router-dom : / (Sélection Univers/Login), /studio (Création de monde avec modales CRUD), /play (Jeu).
   * Le HUD en jeu comprend un **Panneau Latéral** discret pour les stats rapides (HP, AC, Spell slots), et une **Modale** dédiée pour la feuille de personnage complète.
## 6. Conventions de Code et Tests (QA)
 * **SQLModel & Types :** N'utilise JAMAIS from __future__ import annotations. Utilise les imports stricts from typing import List, Optional et la syntaxe de chaîne (List["NomClasse"]) pour éviter les conflits d'enregistrement SQLAlchemy sous Python 3.12.
 * **Tests E2E (End-to-End) :** * Les tests globaux (pytest) doivent utiliser fastapi.testclient.TestClient.
   * **BDD Isolée :** Utilise systématiquement app.dependency_overrides avec une base en mémoire (sqlite:///:memory:) pour protéger les données de production.
   * **Mocks :** Mock toujours les appels réseau asynchrones vers les LLM (unittest.mock.patch) pour des tests rapides et prédictibles.
## 7. Logique Multi-joueurs et Sessions
* **Séparation Identity/Instance :** Un `User` possède des `Characters`. Une `GameSession` instancie un `Universe`. Plusieurs `Characters` peuvent rejoindre une `GameSession`.
* **Authentification (API & Frontend) :** Toutes les routes API (sauf login/register) doivent être protégées par un check de token JWT. **Le Frontend DOIT systématiquement inclure le header `Authorization: Bearer <token>` dans toutes ses requêtes (fetch/axios).**
* **Authentification (WebSocket) :** **Les WebSockets natifs des navigateurs ne supportant pas les headers HTTP personnalisés, le token JWT doit être passé lors de la connexion via un paramètre d'URL (ex: `ws://.../play?token=...`) ou comme tout premier message d'initialisation.**
* **Broadcasting :** Les messages de chat, les changements de `game_mode` et les `STATS_UPDATE` doivent être diffusés à TOUS les participants d'une `GameSession` via le `ConnectionManager`.
* **Persistence de Session :** L'état du combat (X,Y, HP des monstres) doit être sauvé en base de données régulièrement pour permettre la reprise de partie fluide.

