"""Hyperparamètres provisoires du modèle.

Ces valeurs sont des hypothèses d'ingénierie, à calibrer sur des données
de classe et sur un jugement didactique. Elles ne sont pas des normes
d'élève. L'architecture (ontologie, canaux autonome/assisté, règles
d'adaptation) est indépendante de leur réglage fin.
"""

VERSION_MODELE = "0.1.0"

# Pseudo-effectifs du prior de niveau. Huit observations fictives : le prior
# oriente le début, puis les traces réelles le dominent.
KAPPA_PRIOR = 8.0

# Une réponse pleinement surprenante ajoute cette masse, ensuite répartie
# entre les compétences de l'item. Le modulateur de surprise la réduit
# lorsque l'issue était déjà attendue.
UNITE_EVIDENCE = 1.0

# Plancher et pente du modulateur de surprise : une réponse inattendue
# pèse davantage, une réponse attendue pèse encore un peu.
PLANCHER_SURPRISE = 0.40
PENTE_SURPRISE = 0.60

# Écoulement de l'évidence vers le prior lorsqu'aucune observation n'arrive.
# Demi-vie d'environ 69 jours : une période de vacances atténue la certitude
# sans effacer le parcours.
LAMBDA_ECOULEMENT = 0.01

# Lissage de la vitesse d'apprentissage.
RHO_VITESSE = 0.35

# Prédicteur de réussite (échelle logit).
BIAIS_REUSSITE = 0.30
POIDS_COMPETENCE = 0.90
POIDS_STRATEGIE = 0.40
POIDS_DEMANDE = 1.10
POIDS_ECART_LINGUISTIQUE = 0.80
PROCESSUS_SOUTENUS_PAR_STRATEGIE = frozenset({"COH", "INF", "MAC", "EVA"})

# Fenêtre de réussite visée pour l'activité adaptée (zone proximale).
CIBLE_REUSSITE = 0.60

# Seuils de la politique.
SEUIL_PREREQUIS = 0.45
SEUIL_PREUVES_BLOCAGE = 1.0
PREUVES_SONDAGE = 1.0
PENALITE_PREREQUIS = 0.25
ZONE_PROXIMALE = (0.30, 0.82)
FACTEUR_HORS_ZONE = 0.65
PLANCHER_FIABILITE = 0.55
INCERTITUDE_A_SIGNALER = 0.45
PREUVES_CONSOLIDATION = 4.0
INCERTITUDE_CONSOLIDATION_MAX = 0.40

# Engagement de séance.
SEUIL_REPONSE_HATIVE_MS = 4000
TAILLE_SEANCE_ENGAGEMENT = 4
TAUX_HATIF_REGULATION = 0.50
TAUX_REUSSITE_REGULATION = 0.40
TAUX_ABANDON_REGULATION = 0.40

# Méta-cognition : masses faibles, pour ne pas confondre stratégie et score.
MASSE_RELECTURE_REG = 0.15
MASSE_RELECTURE_STR = 0.20
MASSE_CALIBRATION = 0.20
MASSE_CALIBRATION_JUSTE = 0.12
ECART_CALIBRATION_LARGE = 0.55
ECART_CALIBRATION_SERRE = 0.25

# Poids des aides sur les deux canaux de maîtrise.
# Réussite aidée : surtout le canal assisté.
PART_AUTO_REUSSITE_AIDEE = 0.15
PART_ASSISTEE_REUSSITE_AIDEE = 0.85
# Échec malgré l'aide : le canal autonome reste informatif.
PART_AUTO_ECHEC_AIDE = 0.70
PART_ASSISTEE_ECHEC_AIDE = 0.45
# Abandon ou réponse trop rapide : évidence dégradée.
POIDS_ABANDON = 0.40
POIDS_HATIF = 0.30

SEUILS_BANDE = (0.38, 0.50, 0.62, 0.74)
LONGUEUR_MOTS = {
    1: (40, 80),
    2: (70, 130),
    3: (110, 190),
    4: (160, 260),
    5: (220, 380),
}

EFFETS_ETAYAGE = {
    "rappel_strategie": {
        "INF": 0.50,
        "MAC": 0.48,
        "EVA": 0.42,
        "COH": 0.35,
        "VOC": 0.30,
        "STR": 0.40,
        "*": 0.20,
    },
    "segmentation": {
        "SYN": 0.55,
        "EXP": 0.40,
        "DEC": 0.45,
        "FLU": 0.35,
        "COH": 0.30,
        "*": 0.15,
    },
    "connecteurs": {
        "INF": 0.70,
        "COH": 0.65,
        "MAC": 0.30,
        "*": 0.10,
    },
    "modelage": {
        "INF": 0.95,
        "MAC": 0.90,
        "EVA": 0.80,
        "EXP": 0.55,
        "COH": 0.70,
        "SYN": 0.60,
        "VOC": 0.50,
        "STR": 0.70,
        "*": 0.40,
    },
}

THEMES_AUTORISES = ("nature", "animaux", "ecole", "sport", "sciences")

MOTS_STIGMATISANTS = (
    "faible",
    "nul",
    "nulle",
    "mauvais",
    "mauvaise",
    "paresseux",
    "paresseuse",
    "dyslex",
    "en retard",
    "incapable",
    "mauvais lecteur",
    "mauvaise lectrice",
    "problème de comportement",
    "probleme de comportement",
)

REGLES = {
    "R1_REGULATION_ENGAGEMENT": (
        "Les réponses de la séance sont souvent trop rapides et incorrectes, "
        "ou plusieurs tâches sont abandonnées. L'activité est raccourcie et "
        "commence par des questions explicites."
    ),
    "R2_SONDAGE_INCERTITUDE": (
        "Les observations sont encore trop peu nombreuses pour régler une "
        "séance longue. Le modèle propose un court sondage, sans étayage, "
        "afin d'estimer la réussite autonome."
    ),
    "R3_ENRICHISSEMENT": (
        "Les compétences centrales de la compréhension atteignent l'attendu "
        "du niveau avec une incertitude modérée. La proposition s'oriente "
        "vers la justification et le sens global."
    ),
    "R4_CONSOLIDATION_ZPD": (
        "La compétence retenue maximise l'écart à l'attendu du niveau, "
        "parmi les compétences dont les prérequis déjà observés sont disponibles."
    ),
    "R5_RETOUR_PREREQUIS": (
        "La compétence la plus prioritaire s'appuie sur un prérequis encore "
        "fragile et déjà observé. Le travail revient d'abord à ce prérequis."
    ),
    "R6_ETAYAGE_MINIMAL": (
        "L'étayage le plus léger qui atteint la réussite visée est retenu. "
        "S'il n'existe pas, l'étayage le plus engagé de la liste est proposé "
        "avec une mise en garde."
    ),
    "R7_BANDE_LINGUISTIQUE": (
        "La bande du texte suit la reconnaissance des mots, la fluence, le "
        "vocabulaire, la phrase et le prélèvement. Elle décrit le texte du "
        "jour, pas l'identité de l'élève."
    ),
    "R8_DEMANDE_COGNITIVE": (
        "La demande des questions est réglée à part de la difficulté "
        "linguistique du texte : on peut raisonner sur un texte lisible."
    ),
    "R9_VALIDATION_ENSEIGNANTE": (
        "La proposition est soumise à l'enseignant avant d'être présentée "
        "à l'élève."
    ),
    "R10_ANCRE_EXPLICITE": (
        "Le sondage inclut toujours le prélèvement d'une information "
        "explicite, comme repère de la compréhension du texte."
    ),
}
