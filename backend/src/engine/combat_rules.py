import random
from dataclasses import dataclass, replace


@dataclass
class Personnage:
    """Représente un personnage avec ses caractéristiques de base."""
    nom: str
    pv_max: int
    pv_actuels: int
    ca: int
    vitesse: int

    def snapshot(self) -> 'Personnage':
        """Renvoie une copie exacte de l'instance courante pour permettre un rollback."""
        return replace(self)


def roll_dice(sides: int, amount: int = 1) -> int:
    """Lance un nombre donné de dés avec un nombre de faces spécifié.

    Args:
        sides: Le nombre de faces du dé (ex: 20 pour un d20).
        amount: Le nombre de dés à lancer (défaut: 1).

    Returns:
        La somme des résultats des dés lancés. Retourne 0 si amount <= 0 ou sides <= 0.
    """
    if amount <= 0 or sides <= 0:
        return 0
    return sum(random.randint(1, sides) for _ in range(amount))


def resolve_attack(attack_roll: int, base_damage: int, target_ac: int) -> int:
    """Calcule les dégâts infligés par une attaque en comparant le jet d'attaque à la CA cible.

    Ceci est une fonction pure : elle ne modifie pas l'état du personnage.

    Args:
        attack_roll: Le résultat du jet d'attaque (ex: 1d20 + modificateurs).
        base_damage: Les dégâts de base de l'arme ou du sort.
        target_ac: La Classe d'Armure (CA) de la cible.

    Returns:
        Les dégâts infligés (base_damage si attack_roll >= target_ac, sinon 0).
    """
    if attack_roll >= target_ac:
        return base_damage
    return 0
