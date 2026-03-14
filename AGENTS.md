# Documentation et Contexte pour l'Agent de Codage (Jules)
**Projet :** RPG AI Game Master (Application VTT & MJ Virtuel)

## 1. Vision Globale du Projet
L'objectif est de créer une application web (Frontend) et un serveur (Backend) permettant à des joueurs de jouer à un jeu de rôle sur table où le Maître du Jeu (MJ) est incarné par un système d'IA multi-agents. L'application gère l'audio en temps réel, la génération d'histoire, les combats stricts sur une grille (VTT) et la mémoire à long terme.

## 2. Stack Technique Requise
* **Backend :** Python 3.10+, FastAPI (pour l'API REST et les WebSockets).
* **Protocole IA :** Model Context Protocol (MCP) pour la communication entre l'IA et la logique du jeu.
* **Frontend :** React (Vite), Tailwind CSS, WebSockets natifs ou Socket.io.
* **Base de données :** * SQL (PostgreSQL ou SQLite pour le PoC) : Pour les statistiques, l'inventaire, les PV.
    * Vector DB (ChromaDB, Pinecone ou FAISS) : Pour le RAG (Retrieval-Augmented Generation) et la mémoire de l'histoire.

## 3. L'Architecture Multi-Agents & MCP (Le Cerveau)
Le backend utilise le standard MCP pour séparer strictement l'IA de la logique mathématique. L'architecture est la suivante :
1.  **Le Client MCP (L'Agent Narrateur / MJ) :** Le modèle de langage principal. Il lit le contexte, décide des actions narratives et interroge les serveurs MCP.
2.  **Le Routeur d'Intentions :** Analyse chaque phrase du joueur pour déterminer si c'est du Roleplay (RP), une action mécanique, ou une question système, afin d'optimiser les appels.
3.  **Les Serveurs MCP (Outils & Ressources) :**
    * *Serveur Moteur de Jeu :* Expose les outils d'action (ex: `roll_dice`, `calculate_damage`, `move_entity`).
    * *Serveur Mémoire :* Expose les ressources (fiches de personnages SQL) et les prompts (lore via RAG).

## 4. RÈGLES D'OR POUR LA GÉNÉRATION DE CODE (CRITIQUE)
Jules, tu dois impérativement respecter ces principes architecturaux lors de la rédaction du code :

* **Règle n°1 : Le LLM ne fait JAMAIS de mathématiques ou de logique d'état.**
    L'IA ne doit jamais calculer les points de vie, vérifier les portées de déplacement, ou déterminer la réussite d'un jet de dé. Toute cette logique DOIT être codée en Python pur et exposée via un Serveur MCP.
* **Règle n°2 : Utilisation exclusive des Outils MCP.**
    L'Agent Narrateur interagit avec le monde mécanique *uniquement* via les outils fournis par le Serveur MCP. S'il décide qu'un gobelin attaque, il appelle l'outil `attack(source="goblin_1", target="player_1", weapon="short_bow")`. Le serveur exécute la fonction, met à jour la base SQL, et renvoie le résultat au Client MCP.
* **Règle n°3 : La Base de Données est la seule source de vérité.**
    Ne stocke jamais l'état de l'inventaire ou les PV dans le contexte brut du LLM. À chaque tour, l'IA doit lire ces informations en tant que "Ressources" via le protocole MCP.
* **Règle n°4 : Asynchronisme et WebSockets.**
    Le jeu se déroulant en temps réel, toutes les interactions Backend/Frontend doivent passer par des WebSockets asynchrones. Le code Python doit être non-bloquant (utilisation de `async/await`).

## 5. Conventions de Code
* Implémente le MCP en utilisant le SDK officiel Python pour MCP (`mcp`).
* Ajoute des *Type Hints* stricts à toutes les fonctions Python et aux schémas des outils MCP.
* Sépare clairement la configuration des Serveurs MCP (dans le dossier `engine/` et `memory/`) du Client MCP.
* Écris des tests unitaires `pytest` pour chaque outil métier exposé par les Serveurs MCP.
