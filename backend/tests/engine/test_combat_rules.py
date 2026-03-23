import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from engine.combat_rules import Personnage, roll_dice, resolve_attack

def test_roll_dice():
    result = roll_dice(20, 1) # 1d20
    assert type(result) is int
    assert result >= 1 and result <= 20

