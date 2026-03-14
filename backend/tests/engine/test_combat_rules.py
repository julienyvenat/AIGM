import pytest
from src.engine.combat_rules import Personnage, roll_dice, resolve_attack

def test_roll_dice():
    """Vérifie que le jet de dés renvoie des valeurs dans les bornes correctes."""
    # Test avec 1d20
    for _ in range(100):
        result = roll_dice(20, 1)
        assert 1 <= result <= 20

    # Test avec 3d6
    for _ in range(100):
        result = roll_dice(6, 3)
        assert 3 <= result <= 18

    # Cas limites (valeurs négatives ou nulles)
    assert roll_dice(0, 1) == 0
    assert roll_dice(20, 0) == 0
    assert roll_dice(-5, 1) == 0

def test_resolve_attack():
    """Vérifie la résolution des dégâts (Jet >= CA)."""
    # L'attaque touche (Jet > CA)
    assert resolve_attack(15, 8, 12) == 8

    # L'attaque touche tout juste (Jet == CA)
    assert resolve_attack(12, 5, 12) == 5

    # L'attaque rate (Jet < CA)
    assert resolve_attack(10, 10, 14) == 0

def test_personnage_creation_and_snapshot():
    """Vérifie que la création d'un Personnage et la méthode snapshot() fonctionnent correctement."""
    guerrier = Personnage(nom="Grom", pv_max=30, pv_actuels=30, ca=16, vitesse=6)

    assert guerrier.nom == "Grom"
    assert guerrier.pv_max == 30
    assert guerrier.ca == 16

    # Test du snapshot
    snapshot = guerrier.snapshot()
    assert snapshot is not guerrier  # Différentes instances
    assert snapshot.nom == guerrier.nom
    assert snapshot.pv_actuels == guerrier.pv_actuels

    # Vérifie que la modification de l'original n'affecte pas le snapshot
    guerrier.pv_actuels -= 10
    assert guerrier.pv_actuels == 20
    assert snapshot.pv_actuels == 30
