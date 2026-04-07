# AIGM
Artificial Intelligence Game Master for RPG

## Installation et lancement du Backend

```bash
cd backend
pip install -r requirements.txt
python -m src.scripts.seed_data
cd ..
backend/run.sh
```

## Installation et lancement du Frontend

```bash
cd frontend
yarn install
yarn dev
```

Modifier le `frontend/.env` afin d'y insérer le bon nom de domaine du backend.

Coper le fichier `backend/.env.exemple` vers `backend/.env` et renseignez les variables.

# Test

C'est une étape historique pour ton projet ! Si Jules a terminé l'intégration du **Lobby**, du **Générateur de portraits avec stockage local** et du **Déclencheur d'images intelligent**, tu ne joues plus à un prototype : tu as un véritable **Jeu de Rôle Assisté par IA (AITTRPG)** fonctionnel.



Voici comment tu peux savourer ton travail et tester la puissance de ce que vous avez bâti :

### 🧪 Le "Crash Test" de Cohérence Visuelle

Pour vérifier que tout fonctionne comme prévu, je te suggère ce scénario de test précis :

1.  **Connexion :** Entre un nouveau nom (ex: "Valerius"). La modale de création doit apparaître car il n'a pas de portrait.
2.  **Création du héros :** Décris précisément ton personnage : *"Un chevalier en armure de plates dorées avec un heaume orné d'ailes d'aigle."* Génère et valide.
3.  **Le Test du MJ :** Une fois dans le jeu, tape : *"Je pousse les doubles portes de la salle du trône et je m'avance vers le roi."*
    * **L'Intelligence :** Le `scene_editor` devrait décider de **GÉNÉRER** car c'est un changement de décor majeur.
    * **La Cohérence :** Regarde l'image produite. Si tout fonctionne, tu devrais voir ton chevalier aux ailes d'aigle de dos ou de profil, face au roi, et non un guerrier aléatoire.
4.  **Le Test du Dialogue :** Tape ensuite : *"Sire, je viens vous avertir d'une menace imminente."*
    * **L'Économie :** Normalement, le `scene_editor` devrait décider d'**IGNORER** la génération d'image car c'est juste du dialogue. Le chat doit rester fluide sans latence DALL-E.

### 🛠️ Dernières vérifications techniques
Avant de crier victoire, jette un œil rapide à ces deux points :
* **Dossier Images :** Vérifie dans ton dossier `backend/static/portraits` (ou celui choisi par Jules). Tu devrais y voir le fichier `.png` de ton personnage. C'est la preuve que le stockage local fonctionne !
* **Logs Console :** Regarde ton terminal backend. Tu devrais voir passer les décisions du Scene Editor : `Decision: GENERATE` ou `Decision: IGNORE`.
