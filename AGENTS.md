# Documentation et Contexte pour l'Agent de Codage (Jules)
**Projet :** RPG AI Game Master (Application VTT & MJ Virtuel)

## 1. Vision Globale du Projet
L'objectif est de créer une application web (Frontend) et un serveur (Backend) permettant à des joueurs de jouer à un jeu de rôle sur table où le Maître du Jeu (MJ) est incarné par un système d'IA multi-agents. L'application gère l'audio en temps réel, la génération d'histoire, les combats stricts sur une grille (VTT) et la mémoire à long terme.

## 2. Stack Technique Requise
* **Backend :** Python 3.10+, FastAPI (pour l'API REST et les WebSockets).
* **Frontend :** React (Vite), Tailwind CSS, WebSockets natifs ou Socket.io.
* **Base de données :** * SQL (PostgreSQL ou SQLite pour le PoC) : Pour les statistiques, l'inventaire, les PV.
    * Vector DB (ChromaDB, Pinecone ou FAISS) : Pour le RAG (Retrieval-Augmented Generation) et la mémoire de l'histoire.
* **IA & Agents :** Framework type LangChain ou appels d'API directs (OpenAI/Gemini).

## 3. L'Architecture Multi-Agents (Le Cerveau)
Le backend n'utilise pas un seul prompt géant, mais un écosystème d'agents :
1.  **Le Routeur d'Intentions (Fast & Cheap LLM) :** Analyse chaque phrase du joueur. Détermine si c'est du Roleplay (RP), une action mécanique (Attaque), ou une question système. Il route la requête vers le bon sous-système.
2.  **L'Agent Narrateur (Smart LLM) :** Gère la narration principale. Il a accès au contexte global (RAG) et au scénario (fil rouge). Il décrit les scènes et les conséquences.
3.  **L'Agent PNJ :** Instancié dynamiquement avec la personnalité d'un monstre ou d'un marchand précis lorsque les joueurs interagissent avec lui.

## 4. RÈGLES D'OR POUR LA GÉNÉRATION DE CODE (CRITIQUE)
Jules, tu dois impérativement respecter ces principes architecturaux lors de la rédaction du code :

* **Règle n°1 : Le LLM ne fait JAMAIS de mathématiques ou de logique d'état.**
    L'IA ne doit jamais calculer les points de vie, vérifier les portées de déplacement, ou déterminer la réussite d'un jet de dé. Toute cette logique DOIT être codée en Python pur dans le module `engine/`.
* **Règle n°2 : Utilisation massive du Function Calling (Outils).**
    L'Agent Narrateur interagit avec le monde mécanique *uniquement* via des appels de fonctions structurés. S'il décide qu'un gobelin attaque, il génère un appel de fonction `attack(source="goblin_1", target="player_1", weapon="short_bow")`. Le backend Python exécute la fonction, met à jour la base de données SQL, et renvoie le résultat (ex: "12 dégâts subis") au LLM pour qu'il le narre.
* **Règle n°3 : La Base de Données est la seule source de vérité.**
    Ne stocke jamais l'état de l'inventaire ou les PV dans le contexte (historique de chat) du LLM. À chaque tour, le backend doit injecter l'état actuel et factuel des joueurs depuis la base SQL dans le prompt système de l'agent.
* **Règle n°4 : Asynchronisme et WebSockets.**
    Le jeu se déroulant en temps réel, toutes les interactions Backend/Frontend doivent passer par des WebSockets asynchrones. Le code Python doit être non-bloquant (utilisation de `async/await`).

## 5. Conventions de Code
* Ajoute des *Type Hints* stricts à toutes les fonctions Python (ex: `def roll_dice(sides: int) -> int:`).
* Sépare clairement la logique métier (le jeu) de la logique d'infrastructure (FastAPI, WebSockets).
* Écris des tests unitaires `pytest` pour chaque mécanique de jeu ajoutée dans le module `engine/`.
