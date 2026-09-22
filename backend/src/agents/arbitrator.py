import os
import json
from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from google import genai
from google.genai import types

from src.engine.models import Character, GameSystem
from src.engine.dice_tool import roll_dice

class ArbitratorLLMOutput(BaseModel):
    action_type: str = Field(description="Type of action (attack, spell, dodge, skill_check, etc.)")
    narrative: str = Field(description="A brief narrative description of the outcome and the logic used.")
    success: bool = Field(description="Whether the action was a success according to the game system rules.")
    hp_change: int = Field(description="The amount of HP to add (positive) or subtract (negative). 0 if no change.")
    consumed_resource_type: Optional[str] = Field(description="'spell_slot', 'class_resource', or null", default=None)
    consumed_resource_name: Optional[str] = Field(description="e.g. '3' for spell level 3, or 'ki_point'. null if none", default=None)

class ArbitratorResult(BaseModel):
    action_type: str
    narrative: str
    success: bool
    hp_change: int
    consumed_resource_type: Optional[str] = None
    consumed_resource_name: Optional[str] = None

# Configuration OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "")) if os.environ.get("OPENAI_API_KEY") else None
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Configuration Gemini
gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) if os.environ.get("GOOGLE_API_KEY") else None

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

def define_tools():
    """Defines the tools available to the LLM."""
    return [
        {
            "type": "function",
            "function": {
                "name": "roll_dice",
                "description": "Rolls dice according to a provided standard RPG dice expression.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The dice expression to roll (e.g., '1d20+3', '2d6', '1d8-1')."
                        }
                    },
                    "required": ["expression"]
                }
            }
        }
    ]

async def arbitrate_action(character: Character, game_system: GameSystem, intent_text: str) -> ArbitratorResult:
    """
    Use an LLM to determine the success and consequences of an action, using tool calling for dice rolls.
    """
    # 1. Prepare system prompt dynamically
    system_prompt = f"""Tu es l'arbitre du système "{game_system.name}".

Voici le résumé des règles du système :
{game_system.rules_summary}

Règles Spécifiques (CORE RULES) :
{game_system.core_rules_prompt}

Tu ne peux valider l'action d'un joueur que s'il possède le sort dans sa liste et s'il lui reste des emplacements de sorts appropriés.

Le joueur tente l'action suivante : "{intent_text}"

Voici les statistiques actuelles du personnage :
{json.dumps(character.stats, indent=2)}

Inventaire magique et ressources :
Sorts connus: {character.known_spells}
Emplacements de sorts (Niveau: Quantité): {character.spell_slots}
Ressources de classe: {character.class_resources}

Tu DOIS utiliser l'outil `roll_dice` si un jet de dés est requis par les règles pour cette action.
Après avoir obtenu le résultat du jet, ou si aucun jet n'est nécessaire, génère ta réponse finale selon le schéma JSON demandé.
La réponse doit inclure :
- action_type: type d'action
- narrative: Un résumé clair de ce qui s'est passé (ex: "Le joueur a fait 15 au dé (12 + 3 de Force), ce qui dépasse la CA de 14. L'attaque réussit et inflige 6 points de dégâts.")
- success: booléen indiquant si l'action a réussi
- hp_change: perte de HP pour le joueur (négatif) ou gain (positif). Si c'est un jet d'attaque contre un PNJ, le hp_change du joueur est 0 (le MJ gérera les dégâts au PNJ via ton narrative).
- consumed_resource_type / consumed_resource_name
"""

    llm_output = None
    try:
        if LLM_PROVIDER == "gemini":
            if not gemini_client:
                 raise ValueError("GOOGLE_API_KEY is not set.")

            # Define tool for Gemini
            gemini_tools = [{"function_declarations": [{"name": "roll_dice", "description": "Rolls dice according to a provided standard RPG dice expression.", "parameters": {"type": "OBJECT", "properties": {"expression": {"type": "STRING", "description": "The dice expression to roll (e.g., '1d20+3', '2d6')."}}, "required": ["expression"]}}]}]

            chat = gemini_client.aio.chats.create(
                model=GEMINI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=gemini_tools,
                    temperature=0.1
                )
            )

            response = await chat.send_message(intent_text)

            # Check for tool call
            if response.function_calls:
                for function_call in response.function_calls:
                    if function_call.name == "roll_dice":
                        args = function_call.args
                        expression = args.get("expression", "1d20")
                        try:
                            # Execute Python function
                            roll_result = roll_dice(expression)
                            result_str = f"Roll Result for {expression}: Individual: {roll_result.individual_results}, Modifier: {roll_result.modifier}, Total: {roll_result.total}"
                        except Exception as e:
                            result_str = f"Error rolling dice: {str(e)}"

                        # Send result back
                        response = await chat.send_message(
                            types.Part.from_function_response(
                                name="roll_dice",
                                response={"result": result_str}
                            ),
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=ArbitratorLLMOutput,
                            )
                        )
                        break
            else:
                 # If no tool call, we need to enforce structured output for the final response
                 # In Gemini, we might need to send another message to force schema if it didn't
                 # use tool call on first turn but we didn't specify schema on first turn.
                 response = await gemini_client.aio.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=chat.get_history() + [{"role": "user", "parts": ["Veuillez formater votre conclusion finale en JSON selon le schéma demandé."]}],
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=ArbitratorLLMOutput,
                    )
                )

            # Check if text is present
            if response.text:
                 parsed_dict = json.loads(response.text)
                 llm_output = ArbitratorLLMOutput(**parsed_dict)
            else:
                 raise ValueError("Empty response text from Gemini after tool execution")

        else:
            if not client:
                raise ValueError("OPENAI_API_KEY is not set.")

            import asyncio
            loop = asyncio.get_event_loop()

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": intent_text}
            ]

            # Step 1: Call LLM with tools
            def make_first_call():
                return client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=messages,
                    tools=define_tools(),
                    tool_choice="auto",
                )

            response = await loop.run_in_executor(None, make_first_call)
            message = response.choices[0].message
            messages.append(message)

            # Step 2: Handle tool calls
            if getattr(message, "tool_calls", None):
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "roll_dice":
                        arguments = json.loads(tool_call.function.arguments)
                        expression = arguments.get("expression", "1d20")
                        try:
                            roll_result = roll_dice(expression)
                            result_str = f"Roll Result for {expression}: Individual: {roll_result.individual_results}, Modifier: {roll_result.modifier}, Total: {roll_result.total}"
                        except Exception as e:
                            result_str = f"Error rolling dice: {str(e)}"

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_str,
                        })

                # Step 3: Get final parsed output
                def make_second_call():
                    return client.beta.chat.completions.parse(
                        model=DEFAULT_MODEL,
                        messages=messages,
                        response_format=ArbitratorLLMOutput,
                    )
                final_response = await loop.run_in_executor(None, make_second_call)
                llm_output = final_response.choices[0].message.parsed
            else:
                # No tool called, we need to ensure structured output format
                def make_parse_call():
                    # We pop the last assistant message and re-ask with beta.parse
                    msgs = messages[:-1]
                    return client.beta.chat.completions.parse(
                        model=DEFAULT_MODEL,
                        messages=msgs,
                        response_format=ArbitratorLLMOutput,
                    )
                final_response = await loop.run_in_executor(None, make_parse_call)
                llm_output = final_response.choices[0].message.parsed

        if not llm_output:
            raise ValueError("LLM returned empty parsed output.")
    except Exception as e:
        print(f"Error in arbitrator LLM call: {e}")
        # Fallback
        llm_output = ArbitratorLLMOutput(
            action_type="unknown",
            narrative="L'action n'a pas pu être résolue suite à une erreur système.",
            success=False,
            hp_change=0
        )

    return ArbitratorResult(
        action_type=llm_output.action_type,
        narrative=llm_output.narrative,
        success=llm_output.success,
        hp_change=llm_output.hp_change,
        consumed_resource_type=llm_output.consumed_resource_type,
        consumed_resource_name=llm_output.consumed_resource_name
    )
