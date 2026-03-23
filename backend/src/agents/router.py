import os
import json
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI
import google.generativeai as genai

class IntentType(str, Enum):
    ACTION = "ACTION"
    ROLEPLAY = "ROLEPLAY"
    SYSTEM = "SYSTEM"
    IGNORE = "IGNORE"

class PlayerIntent(BaseModel):
    intent: IntentType = Field(
        description="L'intention classifiée de l'action du joueur."
    )
    summary: str = Field(
        description="Résumé très bref de l'action en une phrase"
    )
    target: Optional[str] = Field(
        default=None,
        description="Le nom de la cible s'il y en a une, sinon null"
    )
    action_type: str = Field(
        description="Le type d'action (attack, move, skill_check, dialogue, question, null)"
    )

# Configuration OpenAI (only instantiated if needed or if key exists)
client = OpenAI() if os.environ.get("OPENAI_API_KEY") else None

# Configuration Gemini
if os.environ.get("GOOGLE_API_KEY"):
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

def analyze_player_intent(text: str) -> PlayerIntent:
    """
    Analyse la phrase transcrite d'un joueur et classifie l'intention.
    Retourne un dictionnaire avec 'intent', 'summary', 'target' et 'action_type'.
    Retourne une intention 'IGNORE' par défaut si le parsing échoue.
    """
    system_prompt = """# RÔLE
Tu es l'Analyseur d'Intentions (Router) d'un moteur de jeu de rôle sur table. Ton unique objectif est de lire la retranscription de la voix d'un joueur et de classifier son intention de manière stricte.
TU NE DOIS SOUS AUCUN PRÉTEXTE RÉPONDRE AU JOUEUR. Tu ne dois générer AUCUN texte conversationnel. Ta seule sortie autorisée est un objet JSON valide.

# CATÉGORIES D'INTENTION
Tu dois classer l'entrée du joueur dans l'UNE de ces 4 catégories exactes :
1. "ACTION" : Le joueur déclare vouloir faire quelque chose qui requiert une mécanique de jeu ou qui modifie le monde (attaquer, se déplacer, fouiller une pièce, crocheter, lancer un sort).
2. "ROLEPLAY" : Le joueur parle en tant que son personnage pour dialoguer avec un PNJ, le MJ, ou d'autres joueurs, sans que cela ne demande de jet de dés immédiat (ex: "Bonjour tavernier, une bière !").
3. "SYSTEM" : Le joueur pose une question "hors personnage" (méta) sur les règles, son inventaire ou son état (ex: "Combien de points de vie me reste-t-il ?", "Est-ce que j'ai une potion ?").
4. "IGNORE" : Le joueur fait un bruit, parle à quelqu'un en dehors du jeu, ou dit quelque chose qui ne concerne pas la partie (ex: "Je vais chercher une pizza", "Tu m'entends sur Discord ?").

# FORMAT DE SORTIE (JSON STRICT)
Ta réponse doit être uniquement un JSON respectant la structure suivante :
{
  "intent": "ACTION" | "ROLEPLAY" | "SYSTEM" | "IGNORE",
  "summary": "Résumé très bref de l'action en une phrase",
  "target": "Le nom de la cible s'il y en a une, sinon null",
  "action_type": "attack" | "move" | "skill_check" | "dialogue" | "question" | "null"
}

# EXEMPLES DE CLASSIFICATION (FEW-SHOT PROMPTING)

Entrée joueur : "Je cours vers le gobelin et je lui mets un grand coup de hache !"
Sortie :
{
  "intent": "ACTION",
  "summary": "Le joueur attaque le gobelin avec une hache",
  "target": "gobelin",
  "action_type": "attack"
}

Entrée joueur : "Je dis au garde : 'Laissez-nous passer, nous sommes envoyés par le Roi !'"
Sortie :
{
  "intent": "ROLEPLAY",
  "summary": "Le joueur tente de convaincre le garde de le laisser passer",
  "target": "garde",
  "action_type": "dialogue"
}

Entrée joueur : "Attends, le sort de boule de feu, il a quelle portée déjà ?"
Sortie :
{
  "intent": "SYSTEM",
  "summary": "Le joueur demande la portée du sort boule de feu",
  "target": null,
  "action_type": "question"
}

Entrée joueur : "Ouais, attends deux secondes mon chat vient de renverser mon verre d'eau."
Sortie :
{
  "intent": "IGNORE",
  "summary": "Interruption hors jeu",
  "target": null,
  "action_type": "null"
}"""

    try:
        if LLM_PROVIDER == "gemini":
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=system_prompt
            )
            response = model.generate_content(
                text,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=PlayerIntent,
                )
            )
            parsed_dict = json.loads(response.text)
            return PlayerIntent(**parsed_dict)

        else: # Default to openai
            if not client:
                raise ValueError("OPENAI_API_KEY is not set.")
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format=PlayerIntent,
            )

            parsed_response = response.choices[0].message.parsed
            if parsed_response is None:
                raise ValueError("L'IA n'a pas pu générer un objet JSON valide.")

            return parsed_response

    except Exception as e:
        print(f"Error in router: {e}")
        return PlayerIntent(
            intent=IntentType.IGNORE,
            summary="Erreur de parsing",
            target=None,
            action_type="null"
        )
