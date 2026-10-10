"""Ontologie des compétences de compréhension écrite au primaire.

Les compétences articulent trois cadres compatibles :
- les fondations de la lecture (vue simple de la lecture) ;
- les cinq familles de processus de Giasson ;
- les quatre processus de compréhension de PIRLS.

Les priors et les attendus sont des ancres provisoires par niveau scolaire.
Ils servent à situer un écart pédagogique. Ils ne classent pas un élève.
"""

from __future__ import annotations

from dataclasses import dataclass

from modele_apprenant.constantes import KAPPA_PRIOR


NIVEAUX = ("CP", "CE1", "CE2", "CM1", "CM2")


@dataclass(frozen=True)
class Competence:
    code: str
    libelle: str
    famille: str
    processus_pirls: str | None
    description: str


COMPETENCES: dict[str, Competence] = {
    "DEC": Competence(
        "DEC",
        "Reconnaissance des mots",
        "fondations",
        None,
        "Identifier les mots écrits avec assez d'aisance pour accéder à la phrase.",
    ),
    "FLU": Competence(
        "FLU",
        "Fluence",
        "fondations",
        None,
        "Lire oralement ou silencieusement avec un rythme qui laisse des ressources pour comprendre.",
    ),
    "VOC": Competence(
        "VOC",
        "Vocabulaire en contexte",
        "microprocessus",
        None,
        "Utiliser le contexte et ses connaissances lexicales pour saisir le sens des mots du texte.",
    ),
    "SYN": Competence(
        "SYN",
        "Compréhension de la phrase",
        "microprocessus",
        None,
        "Repérer qui fait quoi dans la phrase, y compris lorsque la syntaxe s'allonge.",
    ),
    "EXP": Competence(
        "EXP",
        "Prélèvement explicite",
        "prelevement",
        "Prélever une information explicitement énoncée",
        "Retrouver dans le texte une information écrite noir sur blanc.",
    ),
    "COH": Competence(
        "COH",
        "Cohésion",
        "integration",
        "Relier des informations proches",
        "Résoudre les reprises (il, elle, ce, les) et suivre les connecteurs entre phrases.",
    ),
    "INF": Competence(
        "INF",
        "Inférences",
        "elaboration",
        "Réaliser des inférences",
        "Comprendre une cause, une intention ou un lien que le texte suggère sans le dire entièrement.",
    ),
    "MAC": Competence(
        "MAC",
        "Sens global",
        "macroprocessus",
        "Interpréter et intégrer",
        "Dégager l'idée principale et l'organisation du texte.",
    ),
    "EVA": Competence(
        "EVA",
        "Justification",
        "elaboration",
        "Examiner et évaluer",
        "Appuyer une interprétation sur un indice du texte et dire ce qui est montré ou seulement suggéré.",
    ),
    "STR": Competence(
        "STR",
        "Stratégies de compréhension",
        "metacognition",
        None,
        "Choisir un geste utile : relire, chercher un connecteur, justifier par un indice.",
    ),
    "REG": Competence(
        "REG",
        "Autorégulation",
        "metacognition",
        None,
        "Repérer une perte de compréhension et ajuster sa confiance à ce que le texte permet vraiment.",
    ),
}

ORDRE: tuple[str, ...] = tuple(COMPETENCES)

# Prérequis forts : on ne centre pas l'activité sur la cible lorsque le
# prérequis est déjà observé et encore fragile.
PREREQUIS: dict[str, tuple[str, ...]] = {
    "FLU": ("DEC",),
    "EXP": ("DEC", "SYN"),
    "COH": ("SYN",),
    "INF": ("EXP", "VOC", "COH"),
    "MAC": ("EXP", "INF"),
    "EVA": ("MAC", "INF"),
}

# Soutiens : ils modulent la réussite estimée sans interdire la cible.
SOUTIENS: dict[str, tuple[str, ...]] = {
    "INF": ("STR",),
    "MAC": ("STR",),
    "EVA": ("STR",),
    "STR": ("REG",),
}

# Étayages du plus léger au plus engagé, parmi ceux qui ont un sens didactique
# pour la compétence focale.
ETAYAGES: dict[str, tuple[str, ...]] = {
    "DEC": ("aucun", "segmentation", "modelage"),
    "FLU": ("aucun", "segmentation"),
    "VOC": ("aucun", "rappel_strategie", "modelage"),
    "SYN": ("aucun", "segmentation", "modelage"),
    "EXP": ("aucun", "segmentation", "modelage"),
    "COH": ("aucun", "connecteurs", "segmentation", "modelage"),
    "INF": ("aucun", "rappel_strategie", "connecteurs", "modelage"),
    "MAC": ("aucun", "rappel_strategie", "modelage"),
    "EVA": ("aucun", "rappel_strategie", "modelage"),
    "STR": ("aucun", "rappel_strategie", "modelage"),
    "REG": ("aucun", "rappel_strategie"),
}

POIDS_LINGUISTIQUES = {
    "DEC": 0.25,
    "FLU": 0.25,
    "VOC": 0.20,
    "SYN": 0.15,
    "EXP": 0.15,
}

# Moyennes de début de parcours, avant traces. Une valeur basse signifie
# « encore peu observé à ce niveau », pas un déficit attribué à l'enfant.
PRIOR: dict[str, dict[str, float]] = {
    "CP": {
        "DEC": 0.40, "FLU": 0.32, "VOC": 0.38, "SYN": 0.34, "EXP": 0.42,
        "COH": 0.32, "INF": 0.28, "MAC": 0.24, "EVA": 0.18, "STR": 0.30, "REG": 0.28,
    },
    "CE1": {
        "DEC": 0.52, "FLU": 0.44, "VOC": 0.44, "SYN": 0.40, "EXP": 0.50,
        "COH": 0.40, "INF": 0.36, "MAC": 0.32, "EVA": 0.24, "STR": 0.36, "REG": 0.32,
    },
    "CE2": {
        "DEC": 0.62, "FLU": 0.52, "VOC": 0.50, "SYN": 0.46, "EXP": 0.58,
        "COH": 0.46, "INF": 0.42, "MAC": 0.36, "EVA": 0.28, "STR": 0.40, "REG": 0.34,
    },
    "CM1": {
        "DEC": 0.72, "FLU": 0.62, "VOC": 0.56, "SYN": 0.52, "EXP": 0.64,
        "COH": 0.54, "INF": 0.50, "MAC": 0.44, "EVA": 0.34, "STR": 0.46, "REG": 0.38,
    },
    "CM2": {
        "DEC": 0.80, "FLU": 0.70, "VOC": 0.62, "SYN": 0.58, "EXP": 0.70,
        "COH": 0.60, "INF": 0.56, "MAC": 0.50, "EVA": 0.40, "STR": 0.50, "REG": 0.42,
    },
}

# Visée de fin de niveau, utilisée comme écart pédagogique. Elle se remplace
# par les attendus locaux de l'équipe enseignante lorsque ceux-ci sont fixés.
ATTENDU: dict[str, dict[str, float]] = {
    "CP": {
        "DEC": 0.58, "FLU": 0.48, "VOC": 0.50, "SYN": 0.46, "EXP": 0.55,
        "COH": 0.45, "INF": 0.40, "MAC": 0.34, "EVA": 0.25, "STR": 0.40, "REG": 0.36,
    },
    "CE1": {
        "DEC": 0.68, "FLU": 0.58, "VOC": 0.55, "SYN": 0.52, "EXP": 0.62,
        "COH": 0.52, "INF": 0.48, "MAC": 0.42, "EVA": 0.30, "STR": 0.46, "REG": 0.40,
    },
    "CE2": {
        "DEC": 0.75, "FLU": 0.65, "VOC": 0.60, "SYN": 0.58, "EXP": 0.68,
        "COH": 0.58, "INF": 0.55, "MAC": 0.48, "EVA": 0.36, "STR": 0.50, "REG": 0.42,
    },
    "CM1": {
        "DEC": 0.82, "FLU": 0.72, "VOC": 0.66, "SYN": 0.62, "EXP": 0.74,
        "COH": 0.64, "INF": 0.62, "MAC": 0.55, "EVA": 0.45, "STR": 0.55, "REG": 0.46,
    },
    "CM2": {
        "DEC": 0.88, "FLU": 0.78, "VOC": 0.70, "SYN": 0.66, "EXP": 0.78,
        "COH": 0.68, "INF": 0.66, "MAC": 0.60, "EVA": 0.52, "STR": 0.58, "REG": 0.50,
    },
}

POIDS_DIDACTIQUE: dict[int, dict[str, float]] = {
    2: {
        "DEC": 1.00, "FLU": 1.15, "VOC": 1.10, "SYN": 1.00, "EXP": 1.20,
        "COH": 1.15, "INF": 1.30, "MAC": 1.15, "EVA": 0.70, "STR": 0.95, "REG": 0.80,
    },
    3: {
        "DEC": 0.70, "FLU": 1.00, "VOC": 1.15, "SYN": 1.05, "EXP": 1.05,
        "COH": 1.10, "INF": 1.25, "MAC": 1.30, "EVA": 1.15, "STR": 1.10, "REG": 0.95,
    },
}

COMPETENCES_CENTRALES = ("FLU", "VOC", "EXP", "INF", "MAC")

LIBELLES_ETAYAGE = {
    "aucun": "aucun étayage pendant la réponse",
    "rappel_strategie": "rappel de stratégie",
    "segmentation": "lecture segmentée",
    "connecteurs": "repérage des connecteurs",
    "modelage": "modelage de la première question",
}

CONSIGNES_ETAYAGE = {
    "aucun": (),
    "rappel_strategie": (
        "Relis la phrase et demande-toi : que puis-je comprendre même si ce n'est pas écrit mot à mot ?",
    ),
    "segmentation": (
        "Lis une phrase, dis ce que tu as compris, puis passe à la suivante.",
    ),
    "connecteurs": (
        "Repère quand, parce que, alors, donc, mais, pour. Ces mots indiquent un lien entre deux idées.",
    ),
    "modelage": (
        "On fait la première question ensemble : on souligne l'indice dans le texte, puis on formule ce qu'il permet de comprendre.",
    ),
}


def cycle_de(niveau: str) -> int:
    if niveau in {"CP", "CE1", "CE2"}:
        return 2
    if niveau in {"CM1", "CM2"}:
        return 3
    raise ValueError(f"Niveau inconnu : {niveau}")


def beta_initiale(niveau: str, code: str) -> tuple[float, float]:
    moyenne = PRIOR[niveau][code]
    moyenne = min(max(moyenne, 0.02), 0.98)
    return moyenne * KAPPA_PRIOR, (1.0 - moyenne) * KAPPA_PRIOR


def attendu(niveau: str, code: str) -> float:
    return ATTENDU[niveau][code]


def poids_didactique(niveau: str, code: str) -> float:
    return POIDS_DIDACTIQUE[cycle_de(niveau)][code]


def libelle(code: str) -> str:
    return COMPETENCES[code].libelle
