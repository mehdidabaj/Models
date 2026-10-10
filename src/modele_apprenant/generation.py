"""Spécification d'activité et générateur par gabarits.

L'IA générative, lorsqu'elle est branchée, ne reçoit que la spécification.
Elle rédige le texte et les questions. Elle ne recalcule pas la maîtrise.
Le générateur par gabarits rend la même spécification sans service externe :
les textes sont originaux, courts, et les réponses attendues sont connues.
"""

from __future__ import annotations

from dataclasses import dataclass

from modele_apprenant.adaptation import DecisionAdaptation
from modele_apprenant.constantes import (
    LONGUEUR_MOTS,
    MOTS_STIGMATISANTS,
    THEMES_AUTORISES,
)
from modele_apprenant.etat import EtatApprenant
from modele_apprenant.ontologie import CONSIGNES_ETAYAGE, LIBELLES_ETAYAGE, libelle


@dataclass(frozen=True)
class SpecificationActivite:
    niveau: str
    theme: str
    theme_demande: str | None
    bande_linguistique: int
    longueur_mots: tuple[int, int]
    demande_cognitive: float
    competence_focale: str
    repartition: dict[str, float]
    etayage: str
    consignes_etayage: tuple[str, ...]
    lecture_adulte_possible: bool
    nombre_questions: int
    contraintes: tuple[str, ...]
    validation_enseignante: bool = True


@dataclass(frozen=True)
class QuestionActivite:
    processus: str
    enonce: str
    reponse_attendue: str
    indice: str


@dataclass(frozen=True)
class QuestionSource:
    processus: str
    enonce: str
    reponse_attendue: str
    indice: str
    phrase_min: int


@dataclass(frozen=True)
class TexteSource:
    theme: str
    titre: str
    phrases: tuple[str, ...]
    questions: tuple[QuestionSource, ...]


@dataclass
class Activite:
    titre: str
    theme: str
    texte: str
    consigne_eleve: str
    questions: list[QuestionActivite]
    observations: list[str]
    note_enseignant: str
    alertes_validation: list[str]

    def texte_eleve(self) -> str:
        lignes = [self.titre, "", self.texte, "", self.consigne_eleve, ""]
        for numero, question in enumerate(self.questions, start=1):
            lignes.append(f"{numero}. {question.enonce}")
        for observation in self.observations:
            lignes.append(f"- {observation}")
        return "\n".join(lignes)

    def texte_enseignant(self) -> str:
        lignes = [self.note_enseignant, "", self.texte_eleve(), "", "Réponses pour l'enseignant"]
        for question in self.questions:
            lignes.append(
                f"- [{question.processus}] {question.reponse_attendue} | indice : {question.indice}"
            )
        return "\n".join(lignes)


NOTES_OBSERVATION = {
    "DEC": "Faire lire deux phrases à voix haute et noter les mots reconnus sans aide.",
    "FLU": "Faire relire le premier paragraphe et écouter le rythme, sans chronométrer devant l'élève.",
    "SYN": "Demander qui fait l'action dans une phrase longue du texte.",
    "STR": "Demander quel indice du texte a été utilisé pour répondre.",
    "REG": "Après une réponse, demander : es-tu sûr, un peu sûr, ou pas sûr ?",
}

NOMBRE_PHRASES = {1: 3, 2: 4, 3: 6, 4: 8, 5: 8}

CONTRAINTES = (
    "Texte original, compréhensible au primaire, sans violence ni humiliation.",
    "Chaque question de compréhension porte un processus demandé par la spécification.",
    "La réponse attendue et l'indice textuel sont fournis à l'enseignant.",
    "Aucun jugement sur l'élève, aucun niveau attribué à l'enfant dans le texte qui lui est lu.",
    "Le générateur ne modifie pas la compétence focale ni les estimations de maîtrise.",
)


def choisir_theme(themes: tuple[str, ...]) -> tuple[str, str | None]:
    for theme in themes:
        if theme in THEMES_AUTORISES:
            return theme, theme
    return "nature", themes[0] if themes else None


def construire_specification(etat: EtatApprenant, decision: DecisionAdaptation) -> SpecificationActivite:
    theme, demande = choisir_theme(etat.profil.themes)
    return SpecificationActivite(
        niveau=etat.profil.niveau,
        theme=theme,
        theme_demande=demande,
        bande_linguistique=decision.bande_linguistique,
        longueur_mots=LONGUEUR_MOTS[decision.bande_linguistique],
        demande_cognitive=decision.demande_cognitive,
        competence_focale=decision.competence_focale,
        repartition=dict(decision.repartition),
        etayage=decision.etayage,
        consignes_etayage=CONSIGNES_ETAYAGE[decision.etayage],
        lecture_adulte_possible=etat.profil.lecture_adulte_possible,
        nombre_questions=decision.nombre_items,
        contraintes=CONTRAINTES,
    )


def construire_prompt(spec: SpecificationActivite) -> str:
    parts = ", ".join(
        f"{code} {poids:.2f}".replace(".", ",") for code, poids in spec.repartition.items()
    )
    lecture = (
        "Le texte peut être lu par l'adulte puis relu par l'élève."
        if spec.lecture_adulte_possible
        else "L'élève lit le texte. Une relecture partielle est possible."
    )
    etayage = " ".join(spec.consignes_etayage) if spec.consignes_etayage else "Pas de consigne d'étayage ajoutée."
    contraintes = " ".join(spec.contraintes)
    return (
        f"Rédige une activité de compréhension écrite pour le {spec.niveau}. "
        f"Thème : {spec.theme}. Bande linguistique : {spec.bande_linguistique} "
        f"({spec.longueur_mots[0]} à {spec.longueur_mots[1]} mots). "
        f"Compétence focale déjà décidée par le modèle symbolique : {libelle(spec.competence_focale)}. "
        f"Répartition des processus : {parts}. "
        f"Étayage : {LIBELLES_ETAYAGE[spec.etayage]}. {etayage} "
        f"{lecture} "
        f"Contraintes : {contraintes} "
        "N'invente aucune maîtrise, aucun score et aucune étiquette d'élève."
    )


TEXTES: dict[str, TexteSource] = {
    "nature": TexteSource(
        theme="nature",
        titre="Les feuilles de Lina",
        phrases=(
            "Lina pose son sac près du grand tilleul de la cour.",
            "Le vent fait tomber trois feuilles jaunes sur son cahier.",
            "Elle les ramasse et les colle sur une page blanche.",
            "Malik sort sans bonnet et touche une feuille.",
            "Il tremble, puis rentre chercher son manteau.",
            "Lina dit que les feuilles jaunes et le vent froid annoncent l'automne.",
            "Le lendemain, la classe observe les feuilles à la loupe.",
            "Lina montre les nervures, sans dire que le vent se voit sur la feuille.",
        ),
        questions=(
            QuestionSource("EXP", "Combien de feuilles tombent sur le cahier ?", "Trois.", "La deuxième phrase dit « trois feuilles jaunes ».", 2),
            QuestionSource("COH", "Dans « Elle les ramasse », que désigne « les » ?", "Les trois feuilles jaunes.", "Elles viennent de tomber sur le cahier.", 3),
            QuestionSource("VOC", "Que désigne le tilleul dans ce texte ?", "Un arbre de la cour.", "Lina pose son sac près du grand tilleul.", 1),
            QuestionSource("INF", "Pourquoi Malik rentre-t-il chercher son manteau ?", "Parce qu'il a froid.", "Il est sorti sans bonnet, il tremble en touchant la feuille.", 5),
            QuestionSource("MAC", "De quoi parle surtout ce texte ?", "Des signes de l'automne observés dans la cour, puis en classe.", "Feuilles, vent froid, puis observation à la loupe.", 6),
            QuestionSource("EVA", "Peut-on dire que Malik est malade ?", "Non. Le texte montre seulement qu'il a froid dehors.", "Il tremble et va chercher un manteau. Aucun mot ne parle d'une maladie.", 8),
        ),
    ),
    "animaux": TexteSource(
        theme="animaux",
        titre="Le hérisson du jardin",
        phrases=(
            "Nora voit un hérisson près du compost du jardin.",
            "Il ne bouge plus quand elle s'approche.",
            "Nora recule et parle doucement.",
            "Le hérisson se remet en route seulement à ce moment-là.",
            "Nora éteint alors sa lampe.",
            "Sa mère explique qu'une lumière vive peut gêner un animal de la nuit.",
            "Le lendemain, Nora laisse une coupelle d'eau loin des croquettes du chat.",
            "Elle dit à son frère que le hérisson a besoin de calme, pas d'un jeu.",
        ),
        questions=(
            QuestionSource("EXP", "Où Nora voit-elle le hérisson ?", "Près du compost du jardin.", "La première phrase le situe.", 1),
            QuestionSource("COH", "Dans « Il ne bouge plus », qui est « il » ?", "Le hérisson.", "La phrase précédente le présente.", 2),
            QuestionSource("VOC", "À quoi sert le compost dans ce jardin ?", "C'est l'endroit près duquel le hérisson a été vu.", "Le texte le place près du compost, sans en faire un jouet.", 1),
            QuestionSource("INF", "Pourquoi le hérisson repart-il quand Nora recule ?", "Parce qu'il se sent moins dérangé.", "Il restait immobile près d'elle, puis il repart quand elle s'éloigne et baisse la voix.", 4),
            QuestionSource("MAC", "Quelle idée principale retenir ?", "Nora apprend à ne pas déranger le hérisson.", "Elle recule, éteint la lampe et parle de calme.", 6),
            QuestionSource("EVA", "Le texte dit-il que le hérisson est un animal de compagnie ?", "Non. Nora le laisse repartir et parle de calme.", "La dernière phrase dit qu'il n'est pas un jeu.", 8),
        ),
    ),
    "ecole": TexteSource(
        theme="ecole",
        titre="Le livre sur les volcans",
        phrases=(
            "Adam entre à la bibliothèque avec un papier dans la main.",
            "Il cherche un livre sur les volcans pour l'exposé du vendredi.",
            "La bibliothécaire lui montre un rayon bas.",
            "Adam ouvre un livre et regarde longtemps une image de lave.",
            "Il chuchote : je vais montrer celle-ci à la classe.",
            "Il emprunte le livre et note la date de retour sur son papier.",
            "Vendredi, il explique le trajet de la lave avec cette image.",
            "Après l'exposé, il rapporte le livre avant la sonnerie.",
        ),
        questions=(
            QuestionSource("EXP", "Pour quel jour Adam prépare-t-il son exposé ?", "Pour vendredi.", "La deuxième phrase donne le jour.", 2),
            QuestionSource("COH", "De qui parle « il » dans « Il cherche un livre » ?", "D'Adam.", "Adam vient d'entrer à la bibliothèque.", 2),
            QuestionSource("VOC", "Que veut dire « exposé » ici ?", "Une présentation pour la classe.", "Adam veut montrer une image et expliquer la lave.", 5),
            QuestionSource("INF", "Pourquoi Adam note-t-il la date de retour ?", "Pour penser à rapporter le livre à temps.", "Il écrit la date sur son papier au moment où il emprunte le livre.", 6),
            QuestionSource("MAC", "Que raconte ce texte ?", "Adam choisit un livre sur les volcans et s'en sert pour son exposé.", "On suit la recherche, le choix de l'image et le retour du livre.", 7),
            QuestionSource("EVA", "Le texte prouve-t-il qu'Adam sait tout sur les volcans ?", "Non. Il montre qu'il explique un trajet de lave avec une image.", "Une seule explication est donnée.", 8),
        ),
    ),
    "sport": TexteSource(
        theme="sport",
        titre="Le relais de la cour",
        phrases=(
            "Quatre élèves préparent un relais dans la cour.",
            "Inès tient le témoin et attend Malik sans partir trop tôt.",
            "Quand il arrive, elle saisit le témoin dans sa main.",
            "Elle court jusqu'au plot bleu, puis s'arrête derrière la ligne.",
            "Le témoin n'est pas tombé pendant l'échange.",
            "Inès sourit et dit : nous avons gardé le témoin ensemble.",
            "La maîtresse propose de boire de l'eau à l'ombre.",
            "L'équipe range les plots avant de rentrer en classe.",
        ),
        questions=(
            QuestionSource("EXP", "Jusqu'où Inès court-elle ?", "Jusqu'au plot bleu.", "La quatrième phrase le dit.", 4),
            QuestionSource("COH", "Dans « Quand il arrive », qui est « il » ?", "Malik.", "Inès attend Malik avec le témoin.", 3),
            QuestionSource("VOC", "Qu'est-ce que le témoin dans ce relais ?", "L'objet que les coureurs se passent.", "Inès le tient, puis le saisit quand Malik arrive.", 3),
            QuestionSource("INF", "Pourquoi Inès sourit-elle après la course ?", "Parce que l'équipe a réussi à garder le témoin.", "Le témoin n'est pas tombé, et elle le dit en souriant.", 6),
            QuestionSource("MAC", "Quel est le sujet du texte ?", "Une équipe s'exerce au relais, puis range le matériel.", "La course est suivie du rangement.", 8),
            QuestionSource("EVA", "Le texte dit-il que cette équipe est la meilleure de l'école ?", "Non. Il raconte un échange de témoin réussi.", "Aucune place ni aucun classement n'est écrit.", 8),
        ),
    ),
    "sciences": TexteSource(
        theme="sciences",
        titre="L'ombre de la règle",
        phrases=(
            "Le matin, la classe plante une règle droite dans la cour.",
            "Nina mesure l'ombre avec un mètre ruban.",
            "L'ombre est courte et tombe vers la classe.",
            "À quatorze heures, la classe revient au même endroit.",
            "L'ombre est plus longue et pointe vers le préau.",
            "Nina regarde le ciel : le Soleil n'est plus au-dessus de la règle.",
            "La maîtresse demande ce qui a changé entre les deux mesures.",
            "Nina écrit que l'ombre a tourné parce que le Soleil a bougé dans le ciel.",
        ),
        questions=(
            QuestionSource("EXP", "Avec quel outil Nina mesure-t-elle l'ombre ?", "Avec un mètre ruban.", "La deuxième phrase le dit.", 2),
            QuestionSource("COH", "Dans « L'ombre est courte », de quelle ombre s'agit-il ?", "De l'ombre de la règle plantée dans la cour.", "La première phrase dit que la classe plante une règle.", 3),
            QuestionSource("VOC", "Que veut dire « mesurer » ici ?", "Trouver la longueur de l'ombre avec un outil.", "Nina utilise un mètre ruban.", 2),
            QuestionSource("INF", "Pourquoi l'ombre n'a-t-elle plus la même place l'après-midi ?", "Parce que le Soleil n'est plus au même endroit dans le ciel.", "Nina voit que le Soleil n'est plus au-dessus de la règle, puis elle l'écrit.", 6),
            QuestionSource("MAC", "Quelle expérience la classe réalise-t-elle ?", "Elle compare l'ombre d'une règle à deux moments du jour.", "Il y a une mesure le matin et une autre à quatorze heures.", 5),
            QuestionSource("EVA", "Une seule mesure suffirait-elle à voir que l'ombre tourne ?", "Non. Il faut comparer le matin et quatorze heures.", "Le changement se voit entre les deux observations.", 8),
        ),
    ),
}


def _selectionner_questions(
    source: TexteSource, spec: SpecificationActivite
) -> list[tuple[QuestionActivite, int]]:
    disponibles = {question.processus: question for question in source.questions}
    utiles = [
        code
        for code, poids in spec.repartition.items()
        if poids >= 0.10 and code in disponibles
    ]
    if spec.competence_focale in disponibles and spec.competence_focale not in utiles:
        utiles.insert(0, spec.competence_focale)
    questions: list[tuple[QuestionActivite, int]] = []
    for processus in utiles:
        question = disponibles[processus]
        questions.append(
            (
                QuestionActivite(
                    question.processus,
                    question.enonce,
                    question.reponse_attendue,
                    question.indice,
                ),
                question.phrase_min,
            )
        )
    return questions


def _observations(spec: SpecificationActivite) -> list[str]:
    return [
        NOTES_OBSERVATION[code]
        for code, poids in spec.repartition.items()
        if poids >= 0.10 and code in NOTES_OBSERVATION
    ]


class GenerateurParGabarits:
    """Rendu local, remplaçable par un générateur génératif sous la même spécification."""

    def generer(self, spec: SpecificationActivite) -> Activite:
        source = TEXTES[spec.theme]
        selection = _selectionner_questions(source, spec)
        nombre_bande = NOMBRE_PHRASES[spec.bande_linguistique]
        besoin = max((phrase_min for _, phrase_min in selection), default=1)
        nombre = min(len(source.phrases), max(nombre_bande, besoin))
        texte = " ".join(source.phrases[:nombre])
        consignes = list(spec.consignes_etayage)
        if spec.lecture_adulte_possible:
            consignes.append(
                "Le texte peut être lu à voix haute par l'adulte, puis relu par l'élève."
            )
        consigne = "Lis le texte, puis réponds aux questions."
        if consignes:
            consigne = f"{consigne} {' '.join(consignes)}"
        note = (
            f"Activité gabarit, bande {spec.bande_linguistique}, "
            f"focale « {libelle(spec.competence_focale)} », "
            f"étayage : {LIBELLES_ETAYAGE[spec.etayage]}. "
            "À valider avant passation."
        )
        if nombre > nombre_bande:
            note += (
                " Le passage du gabarit a été étendu pour que l'indice de la question "
                "focale figure dans le texte. Un générateur rédactionnel devra tenir "
                "la longueur de bande tout en conservant cet indice."
            )
        return Activite(
            titre=source.titre,
            theme=spec.theme,
            texte=texte,
            consigne_eleve=consigne,
            questions=[question for question, _ in selection],
            observations=_observations(spec),
            note_enseignant=note,
            alertes_validation=[],
        )


def valider_activite(activite: Activite, spec: SpecificationActivite) -> list[str]:
    alertes: list[str] = []
    if activite.theme != spec.theme:
        alertes.append("Le thème de l'activité diffère de la spécification.")
    if not activite.questions and not activite.observations:
        alertes.append("L'activité ne contient ni question ni observation.")
    processus_spec = set(spec.repartition)
    for question in activite.questions:
        if question.processus not in processus_spec:
            alertes.append(
                f"La question « {question.enonce} » porte le processus {question.processus}, absent de la spécification."
            )
        if not question.reponse_attendue or not question.indice:
            alertes.append(f"La question « {question.enonce} » n'a pas de réponse attendue ou d'indice.")
    if spec.competence_focale in {q.processus for q in TEXTES[spec.theme].questions}:
        if spec.competence_focale not in {q.processus for q in activite.questions}:
            alertes.append("La compétence focale ne apparaît dans aucune question.")
    corpus = activite.texte_eleve().lower()
    for mot in MOTS_STIGMATISANTS:
        if mot in corpus:
            alertes.append(f"Formulation à écarter du texte élève : {mot}.")
    return alertes
