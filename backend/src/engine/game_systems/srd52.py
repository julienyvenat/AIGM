"""Définition du système D&D SRD 5.2 (contenu data-driven, injecté dans les prompts).

Le backend ne contient aucune règle codée en dur : tout est dans ces textes et ce schéma.

Attribution : ce travail comprend des éléments du System Reference Document 5.2
(« SRD 5.2 ») de Wizards of the Coast LLC, disponible sur
https://www.dndbeyond.com/srd. Le SRD 5.2 est placé sous licence Creative Commons
Attribution 4.0 International (https://creativecommons.org/licenses/by/4.0/legalcode).
Ce texte est un résumé de travail en français, non une reproduction intégrale du SRD.
"""

SRD52_NAME = "D&D SRD 5.2"

SRD52_DESCRIPTION = (
    "Dungeons & Dragons — System Reference Document 5.2 (règles 2024), "
    "licence CC-BY-4.0. Système fantastique basé sur le d20."
)

SRD52_ATTRIBUTION = (
    "Ce travail comprend des éléments du System Reference Document 5.2 de Wizards of the Coast LLC "
    "(https://www.dndbeyond.com/srd), sous licence Creative Commons Attribution 4.0 International "
    "(https://creativecommons.org/licenses/by/4.0/legalcode)."
)

SRD52_RULES_SUMMARY = """# D&D SRD 5.2 — Résumé des règles
**Test de d20 :** d20 + modificateur de caractéristique + bonus de maîtrise (si maîtrisé) contre un DD (test de caractéristique, jet de sauvegarde) ou une CA (jet d'attaque). Égaler ou dépasser réussit.
**Modificateur :** (valeur - 10) / 2, arrondi à l'inférieur.
**Bonus de maîtrise :** +2 (niv. 1-4), +3 (5-8), +4 (9-12), +5 (13-16), +6 (17-20).
**Avantage / Désavantage :** 2d20, garder le plus haut / le plus bas. Ils s'annulent s'il y a les deux, sans cumul.
**20 / 1 naturel :** un 20 naturel sur un jet d'attaque est un coup critique (dés de dégâts doublés) et touche toujours ; un 1 naturel rate toujours.
**Inspiration héroïque :** peut être dépensée pour relancer un d20 (on garde le nouveau résultat).
**Combat :** initiative (test de DEX), tour = déplacement + 1 action + 1 action bonus (si disponible) ; 1 réaction par round ; attaque d'opportunité en quittant la portée d'un ennemi.
**Points de vie :** à 0 PV, inconscient et jets de sauvegarde contre la mort (DD 10 : 3 succès = stabilisé, 3 échecs = mort ; 20 naturel = 1 PV).
**Repos :** court (1 h) pour dépenser des dés de vie ; long (8 h) restaure PV, moitié des dés de vie et emplacements de sorts.
**Épuisement :** niveaux cumulatifs ; chaque niveau donne -2 aux tests de d20 et -5 pieds de vitesse par niveau ; mort au niveau 6.
"""

SRD52_CORE_RULES_PROMPT = """Tu es l'Arbitre d'une partie de Donjons & Dragons selon le SRD 5.2 (règles 2024). Applique ces règles strictement ; tout calcul est fait par le moteur de jeu et les outils de dés, jamais « de tête ».

## Résolution (test de d20)
- Test de d20 = d20 + modificateur de caractéristique (+ bonus de maîtrise si le personnage maîtrise la compétence, l'outil, le jet de sauvegarde ou l'arme). Réussite si total >= DD (ou CA pour une attaque).
- Modificateur = floor((valeur - 10) / 2). Bonus de maîtrise : +2 (niv. 1-4), +3 (5-8), +4 (9-12), +5 (13-16), +6 (17-20).
- DD usuels : très facile 5, facile 10, moyen 15, difficile 20, très difficile 25, quasi impossible 30.
- Avantage : lance 2d20, garde le plus haut. Désavantage : garde le plus bas. Avantage et désavantage se neutralisent (jamais de cumul). Attribue-les selon le contexte décrit par le Narrateur.
- Compétences (caractéristique) : Acrobaties (DEX), Arcanes (INT), Athlétisme (FOR), Discrétion (DEX), Dressage (SAG), Escamotage (DEX), Histoire (INT), Intimidation (CHA), Intuition (SAG), Investigation (INT), Médecine (SAG), Nature (INT), Perception (SAG), Persuasion (CHA), Religion (INT), Représentation (CHA), Supercherie (CHA), Survie (SAG).
- Inspiration héroïque : un personnage qui en dispose peut la dépenser pour relancer un de ses d20 et doit garder le nouveau résultat.

## Combat
- Initiative : test de DEX de chaque combattant, ordre décroissant. Un round dure environ 6 secondes.
- À son tour : déplacement (vitesse), 1 action, 1 action bonus seulement si une capacité l'autorise, interaction gratuite avec un objet. 1 réaction par round (ex. attaque d'opportunité quand une créature quitte la portée sans Désengagement).
- Actions : Attaquer, Lancer un sort, Se précipiter, Se désengager, Esquiver, Aider, Se cacher, Chercher, Se préparer, Utiliser un objet, Influencer, Étudier, Magie.
- Jet d'attaque = d20 + modificateur de caractéristique + maîtrise (si maîtrisé) contre la CA. 20 naturel : coup critique, touche toujours, les dés de dégâts sont doublés. 1 naturel : rate toujours.
- Dégâts = dés de l'arme/du sort + modificateur de caractéristique (sauf indication contraire). Types : contondant, perforant, tranchant, acide, froid, feu, force, foudre, nécrotique, poison, psychique, radiant, tonnerre. Résistance : dégâts divisés par 2 ; vulnérabilité : doublés ; immunité : nuls.
- Maîtrises d'armes (Weapon Mastery) : applique la propriété de maîtrise de l'arme (Entaille, Ébranlement, Enchevêtrement, Poussée, Ralentissement, Sape, Vexation, Affaiblissement, Ouverture) uniquement si le personnage possède cette maîtrise.
- Abri : demi-abri +2 à la CA et aux sauvegardes de DEX ; trois-quarts +5 ; abri total : ne peut être ciblé directement.
- Attaque à mains nues : 1 + mod. FOR dégâts contondants (ou empoignade / bousculade au choix de l'attaquant).
- Combat monté, sous l'eau, à distance (désavantage au-delà de la portée normale ou si un ennemi est adjacent) : applique les règles standard du SRD.

## Jets de sauvegarde
- d20 + modificateur de la caractéristique + maîtrise si maîtrisé, contre le DD du sort/effet. DD de sort = 8 + mod. de la caractéristique d'incantation + bonus de maîtrise. Attaque de sort = d20 + mod. d'incantation + maîtrise.

## Points de vie, mort et repos
- À 0 PV : le personnage est inconscient. Jets de sauvegarde contre la mort à chaque tour : d20 sans modificateur, DD 10 ; 3 succès = stabilisé, 3 échecs = mort ; 20 naturel = revient à 1 PV ; 1 naturel = 2 échecs ; subir des dégâts = 1 échec (2 sur critique). Dégâts restants >= PV max = mort instantanée.
- Repos court (1 h minimum) : dépenser des dés de vie pour regagner des PV (dé + mod. CON). Repos long (8 h minimum, 1 par 24 h) : tous les PV, la moitié des dés de vie dépensés (min. 1), tous les emplacements de sorts, réduit l'épuisement d'un niveau.

## États
Aveuglé, Charmé, Assourdi, Épuisé (cumulatif : -2 × niveau aux tests de d20, -5 pi de vitesse × niveau, mort au niveau 6), Effrayé, Agrippé, Neutralisé, Invisible, Paralysé, Pétrifié, Empoisonné, À terre, Entravé, Étourdi, Inconscient. Applique les effets mécaniques standard du SRD pour chacun.

## Magie
- Emplacements de sorts consommés selon le niveau du sort ; les tours de magie (niveau 0) sont gratuits. Surcharger un emplacement de niveau supérieur applique l'effet « à plus haut niveau ».
- Concentration : un seul sort de concentration à la fois ; en cas de dégâts, jet de sauvegarde de CON, DD = max(10, moitié des dégâts), sinon le sort prend fin. Concentration rompue si incapacité ou mort.
- Une seule action bonus de sort par tour et, si un sort est lancé en action bonus, seul un tour de magie peut être lancé avec l'action.

## Règles d'arbitrage
- Ne décide jamais du résultat narratif : renvoie la mécanique (jets, DD, dégâts, ressources consommées) et laisse le Narrateur décrire.
- Choisis la caractéristique et la compétence les plus pertinentes ; en cas de doute, favorise l'action la plus fluide et dramatiquement intéressante.
- Pour toute créature absente des données de la partie, utilise les valeurs du SRD ou des estimations raisonnables cohérentes avec son niveau de menace (DD 8 + maîtrise + mod.).
"""

SRD52_CHARACTER_SCHEMA = {
    "STR": "Force - Puissance physique (athlétisme)",
    "DEX": "Dextérité - Agilité, réflexes, initiative",
    "CON": "Constitution - Santé et endurance",
    "INT": "Intelligence - Raisonnement et mémoire",
    "WIS": "Sagesse - Perception et intuition",
    "CHA": "Charisme - Force de personnalité",
    "HP": "Points de vie actuels",
    "AC": "Classe d'armure",
}

SRD52_DICE_SYSTEM = "d20"
