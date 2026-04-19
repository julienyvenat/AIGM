# AIGM
Artificial Intelligence Game Master for RPG

## Installation et lancement du Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.scripts.seed_data
cd ..
backend/run.sh
```

## Installation et lancement du Frontend

```bash
cd frontend
npm install
npm run build
```

Modifier le `frontend/.env` afin d'y insérer le bon nom de domaine du backend.

Copiez le fichier `backend/.env.exemple` vers `backend/.env` et renseignez les variables.

**Nouveauté (Auth & Personnages) :**
Toutes les requêtes vers le backend nécessitent désormais une authentification par JWT. Les requêtes via l'interface utilisent un intercepteur (`apiFetch`). Si vous effectuez des appels manuels vers l'API, assurez-vous de passer le header `Authorization: Bearer <votre_token>`.

# Test

C'est une étape historique pour ton projet ! Si Jules a terminé l'intégration du **Lobby**, du **Générateur de portraits avec stockage local**, du **Déclencheur d'images intelligent** et **des flux d'authentification des Sessions**, tu ne joues plus à un prototype : tu as un véritable **Jeu de Rôle Assisté par IA (AITTRPG)** fonctionnel.

Voici comment tu peux savourer ton travail et tester la puissance de ce que vous avez bâti :

### 🧪 Le "Crash Test" de Cohérence et d'Intégration (Session & Personnages)

Pour vérifier que tout fonctionne comme prévu, je te suggère ce scénario de test précis :

1.  **Enregistrement / Connexion :** Créez un compte ou connectez-vous.
2.  **Création du héros (Dashboard) :** Dans le nouveau Dashboard, sélectionnez un Univers et nommez votre personnage (ex: "Valerius").
3.  **Lancement (Home) :** Allez sur "Sélection Univers", sélectionnez votre Univers, puis choisissez "Valerius" pour lancer une nouvelle partie. La session vous sera associée.
4.  **Le Test du MJ :** Une fois dans le jeu, tape : *"Je pousse les doubles portes de la salle du trône et je m'avance vers le roi."*
    * **L'Intelligence :** Le `scene_editor` devrait décider de **GÉNÉRER** car c'est un changement de décor majeur.
5.  **Le Test du Dialogue :** Tape ensuite : *"Sire, je viens vous avertir d'une menace imminente."*
    * **L'Économie :** Normalement, le `scene_editor` devrait décider d'**IGNORER** la génération d'image car c'est juste du dialogue. Le chat doit rester fluide sans latence LLM/Image.

### 🛠️ Dernières vérifications techniques
Avant de crier victoire, jette un œil rapide à ces deux points :
* **Dossier Images :** Vérifie dans ton dossier `backend/images`. Tu devrais y voir le fichier `.png` de ton personnage ou de tes scènes.
* **Console Network :** Vérifiez sur le navigateur que vos appels partent bien avec le Header `Authorization: Bearer <votre_token>`.
* **Tests unitaires de sécurité :** Exécutez `export PYTHONPATH=backend && pytest backend/test_integration.py` pour valider que le backend repousse correctement (code HTTP 403) un utilisateur essayant de se connecter avec le personnage d'un autre joueur.

## Modèles de données

Le système utilise désormais une approche agnostique pour la gestion des statistiques et des attributs de jeu.
* `GameSystem` : Définit les systèmes de règles avec des prompts de règles intégrés (`core_rules_prompt`) et la structure attendue des personnages (`character_schema`).
* `Character` : Les statistiques spécifiques (Force, Intelligence, etc.) ont été remplacées par un champ JSON flexible (`stats`), permettant de s'adapter dynamiquement au schéma défini par le système de jeu de l'univers.
* `Item` : Les propriétés variables comme les dégâts, le poids ou la rareté sont stockées dans un champ JSON `attributes` pour s'adapter à n'importe quel système.
