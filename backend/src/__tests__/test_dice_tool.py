import pytest
from src.engine.tools.dice_tool import roll_dice, DiceRollResult

def test_roll_dice_simple():
    result = roll_dice("1d20")
    assert isinstance(result, DiceRollResult)
    assert result.expression == "1d20"
    assert len(result.individual_results) == 1
    assert 1 <= result.individual_results[0] <= 20
    assert result.modifier == 0
    assert result.total == result.individual_results[0]

def test_roll_dice_addition():
    result = roll_dice("1d20+5")
    assert result.modifier == 5
    assert len(result.individual_results) == 1
    assert result.total == result.individual_results[0] + 5

def test_roll_dice_subtraction():
    result = roll_dice("2d6-2")
    assert result.modifier == -2
    assert len(result.individual_results) == 2
    assert result.total == sum(result.individual_results) - 2

def test_roll_dice_multiple_pools():
    result = roll_dice("1d20 + 1d4 + 3")
    assert len(result.individual_results) == 2
    assert result.modifier == 3
    assert result.total == sum(result.individual_results) + 3

def test_roll_dice_implied_count():
    result = roll_dice("d20")
    assert len(result.individual_results) == 1
    assert 1 <= result.individual_results[0] <= 20

def test_roll_dice_spaces():
    result = roll_dice(" 1 d 20 + 3 ")
    assert len(result.individual_results) == 1
    assert result.modifier == 3

def test_roll_dice_invalid_syntax():
    with pytest.raises(ValueError, match="Invalid token in expression"):
        roll_dice("1d20 + abc")

def test_roll_dice_invalid_sides():
    with pytest.raises(ValueError, match="Invalid number of sides"):
        roll_dice("1d0")

def test_roll_dice_invalid_dice_count():
    with pytest.raises(ValueError, match="Invalid number of dice"):
        roll_dice("0d20")
