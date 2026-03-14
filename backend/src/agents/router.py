import json
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI

class IntentType(str, Enum):
    ROLEPLAY = "ROLEPLAY"
    ACTION = "ACTION"
    SYSTEM = "SYSTEM"

class PlayerIntent(BaseModel):
    intent: IntentType = Field(
        description="L'intention classifiée de l'action du joueur."
    )
    target_entity: Optional[str] = Field(
        default=None,
        description="L'entité visée par l'action (ex: 'marchand', 'goblins 3'). null si aucune entité n'est visée."
    )

# Assurez-vous d'avoir configuré la variable d'environnement OPENAI_API_KEY
client = OpenAI()

def analyze_player_intent(text: str) -> dict:
    """
    Analyse la phrase transcrite d'un joueur et classifie l'intention.
    Retourne un dictionnaire avec 'intent' ('ROLEPLAY', 'ACTION', 'SYSTEM') et 'target_entity'.
    Lève une exception si le texte est incompréhensible ou si l'IA échoue à renvoyer le JSON.
    """
    prompt = f"""
Tu es un assistant IA pour une application de Maître du Jeu de JdR (RPG).
Ta tâche est de classifier la phrase transcrite d'un joueur dans l'une des trois catégories suivantes :

- ROLEPLAY : Parler à un PNJ, interagir socialement, menacer, etc.
  Exemple : "j'attrape la main du marchand et le menace de l'embrocher s'il essaye de nous arnaquer." -> target_entity: "marchand"
- ACTION : Mouvements physiques, attaquer, lancer un sort, ou effectuer une tâche physique.
  Exemple : "je me déplace de 6 pas vers l'avant." -> target_entity: null
- SYSTEM : Questions sur les règles, application de dégâts, modification de statistiques.
  Exemple : "Réduire les points de vie du goblins 3 de 5 PV" -> target_entity: "goblins 3"

Analyse le texte suivant et retourne uniquement un objet JSON contenant l'intention et l'entité visée.
Si la phrase est totalement incompréhensible ou hors contexte, l'analyse doit échouer (le format strict refusera les valeurs hors IntentType).

Texte à analyser :
"{text}"
"""

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant utile qui extrait l'intention d'un joueur de JdR sous forme de JSON structuré."
                },
                {"role": "user", "content": prompt}
            ],
            response_format=PlayerIntent,
        )

        parsed_response = response.choices[0].message.parsed
        if parsed_response is None:
            raise ValueError("L'IA n'a pas pu générer un objet JSON valide.")

        return parsed_response.model_dump()

    except Exception as e:
        raise Exception(f"Échec de l'analyse de l'intention du joueur : {str(e)}") from e
