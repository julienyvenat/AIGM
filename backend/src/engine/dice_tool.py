import re
import secrets
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class DiceRollResult(BaseModel):
    expression: str = Field(..., description="The original dice expression parsed")
    individual_results: List[int] = Field(..., description="The individual results of the dice rolls")
    modifier: int = Field(..., description="The total modifier applied")
    total: int = Field(..., description="The final calculated total")

def roll_dice(expression: str) -> DiceRollResult:
    """
    Rolls dice according to a provided standard RPG dice expression.

    This tool parses a dice string, simulates the rolls, and returns a structured result.

    Args:
        expression (str): The dice expression to roll. Supported formats include simple
                          expressions like '1d20', '2d6+3', '1d8-1', as well as multiple
                          dice pools like '1d20+1d4+2'. Spaces in the expression are ignored.
                          Format components:
                          - XdY: Rolls X dice with Y sides (e.g., '2d6').
                          - +Z or -Z: Adds or subtracts a static modifier (e.g., '+3').

    Returns:
        DiceRollResult: A Pydantic model containing:
            - expression (str): The original expression string.
            - individual_results (List[int]): The raw values rolled on the dice.
            - modifier (int): The total static modifier applied (+ or -).
            - total (int): The final sum of all dice and the modifier.

    Raises:
        ValueError: If the expression contains invalid syntax or unsupported formats.
    """
    # Remove all spaces
    expr = expression.replace(" ", "").lower()

    # Split the expression by '+' and '-', keeping the delimiters
    # Using re.split with capture groups keeps the delimiters in the resulting list
    tokens = re.split(r'([+-])', expr)

    # Handle the case where the expression starts with a + or -
    if not tokens[0]:
        tokens.pop(0)
    else:
        # If it doesn't start with a sign, implicitly it's positive
        tokens.insert(0, '+')

    if not tokens:
        raise ValueError("Empty dice expression")

    individual_results: List[int] = []
    total_modifier = 0
    total = 0

    # Process tokens in pairs: [sign, value]
    i = 0
    while i < len(tokens):
        sign_str = tokens[i]
        value_str = tokens[i+1]

        sign_multiplier = 1 if sign_str == '+' else -1

        # Check if it's a dice roll (XdY)
        dice_match = re.match(r'^(\d*)d(\d+)$', value_str)
        if dice_match:
            count_str = dice_match.group(1)
            num_dice = int(count_str) if count_str else 1
            num_sides = int(dice_match.group(2))

            if num_sides < 1:
                 raise ValueError(f"Invalid number of sides: {num_sides}")
            if num_dice < 1:
                 raise ValueError(f"Invalid number of dice: {num_dice}")

            for _ in range(num_dice):
                roll = secrets.randbelow(num_sides) + 1
                # Keep the roll positive in individual results, apply sign to total
                individual_results.append(roll)
                total += roll * sign_multiplier
        # Check if it's a static modifier
        elif re.match(r'^\d+$', value_str):
            modifier = int(value_str)
            total_modifier += modifier * sign_multiplier
            total += modifier * sign_multiplier
        else:
            raise ValueError(f"Invalid token in expression: {value_str}")

        i += 2

    return DiceRollResult(
        expression=expression,
        individual_results=individual_results,
        modifier=total_modifier,
        total=total
    )
