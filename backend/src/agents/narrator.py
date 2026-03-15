import json
import os
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from backend.src.engine.tools import get_combat_state, move_entity, execute_attack, roll_dice

# Initialize OpenAI client with API key from environment
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

NARRATOR_SYSTEM_PROMPT = """Tu es un Maître du Jeu de jeu de rôle. Tu gères le monde, l'histoire et les PNJ. Tu as accès à des outils pour interagir avec le moteur de jeu strict (déplacements, attaques, dés). Tu ne dois JAMAIS inventer le résultat d'une action mécanique, tu dois utiliser les outils pour ça, puis narrer le résultat de manière immersive et concise."""

GAME_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_combat_state",
            "description": "Returns a list of all Characters with their coordinates, HP, and PC status. Use this to know where everyone is and their health.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_entity",
            "description": "Moves an entity to specific coordinates. Checks if the target is within the character's speed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The UUID of the entity to move."
                    },
                    "target_x": {
                        "type": "integer",
                        "description": "The target X coordinate."
                    },
                    "target_y": {
                        "type": "integer",
                        "description": "The target Y coordinate."
                    }
                },
                "required": ["entity_id", "target_x", "target_y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_attack",
            "description": "Executes an attack from an attacker to a target. Handles to-hit rolls, weapon damage dice, and HP reduction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attacker_id": {
                        "type": "string",
                        "description": "The UUID of the attacking entity."
                    },
                    "target_id": {
                        "type": "string",
                        "description": "The UUID of the target entity."
                    }
                },
                "required": ["attacker_id", "target_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "roll_dice",
            "description": "Parse dice notation like '1d20+3' and return the numeric result. Use this for general skill checks or arbitrary rolls not covered by attacks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "notation": {
                        "type": "string",
                        "description": "The dice notation, e.g., '1d20', '2d6+2'."
                    }
                },
                "required": ["notation"]
            }
        }
    }
]

async def generate_narrator_response(session: AsyncSession, player_id: str, text: str, context: str = "") -> str:
    messages = [
        {"role": "system", "content": NARRATOR_SYSTEM_PROMPT}
    ]

    if context:
        messages.append({"role": "system", "content": f"{context}"})

    messages.append({"role": "user", "content": text})

    while True:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=GAME_TOOLS,
        )

        message = response.choices[0].message

        # If no tool calls, we're done
        if not message.tool_calls:
            return message.content

        # Append the assistant's message with the tool_calls to the conversation history
        messages.append(message.model_dump())

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}

            tool_response_content = ""
            try:
                if tool_name == "get_combat_state":
                    result = await get_combat_state(session)
                    tool_response_content = json.dumps(result)

                elif tool_name == "move_entity":
                    entity_id_uuid = uuid.UUID(args["entity_id"])
                    target_x = args["target_x"]
                    target_y = args["target_y"]
                    result = await move_entity(session, entity_id_uuid, target_x, target_y)
                    tool_response_content = json.dumps(result)

                elif tool_name == "execute_attack":
                    attacker_id_uuid = uuid.UUID(args["attacker_id"])
                    target_id_uuid = uuid.UUID(args["target_id"])
                    result = await execute_attack(session, attacker_id_uuid, target_id_uuid)
                    tool_response_content = str(result)

                elif tool_name == "roll_dice":
                    notation = args["notation"]
                    result = roll_dice(notation)
                    tool_response_content = str(result)
                else:
                    tool_response_content = f"Error: Unknown tool {tool_name}"
            except Exception as e:
                # Capture errors and send them back to the AI
                tool_response_content = str(e)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_response_content,
            })
