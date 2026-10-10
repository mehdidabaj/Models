"""Explications destinées à l'enseignant, à l'élève et à la famille.

L'explication retrace les règles réellement déclenchées et les estimations
du modèle symbolique. Elle ne produit pas un second diagnostic.
"""

from __future__ import annotations

from dataclasses import dataclass

from modele_apprenant.adaptation import DecisionAdaptation, decider, regulation_engagee
from modele_apprenant.analytique import IndicateursSeance
from modele_apprenant.constantes import REGLES
from modele_apprenant.etat import EtatApprenant
from modele_apprenant.ontologie import libelle


PUBLICS = ("enseignant", "eleve", "famille")


@dataclass(frozen=True)
class Explication:
    public: str
    resume: str
    constats: tuple[str, ...]
    raisons: tuple[str, ...]
    limites: tuple[str, ...]
    contrefactuels: tuple[str, ...]
    texte: str


def _fmt(valeur: float) -> str:
    return f"{valeur:.2f}".replace(".", ",")


def _qualite_tendance(vitesse: float) -> str:
    if vitesse > 0.01:
        return "en progression sur les dernières réponses"
    if vitesse < -0.01:
        return "en recul sur les dernières réponses"
    return "stable sur les dernières réponses"


def _contrefactuel(
    etat: EtatApprenant,
    decision: DecisionAdaptation,
    indicateurs: IndicateursSeance,
) -> str:
    nom = libelle(decision.competence_focale)
    if regulation_engagee(indicateurs):
        return (
            f"Même si « {nom} » était estimée à 0,85, le déroulement de cette séance "
            "maintiendrait une activité courte, avec un démarrage sur des questions explicites."
        )
    alternatif = etat.copier()
    alternatif.fixer_maitrise(
        decision.competence_focale,
        0.85,
        preuves=max(etat.preuves(decision.competence_focale), 8.0),
    )
    autre = decider(alternatif, indicateurs)
    if (
        autre.competence_focale == decision.competence_focale
        and autre.type_decision == decision.type_decision
    ):
        return (
            f"Avec une maîtrise autonome de 0,85 en « {nom} », la proposition resterait "
            f"de type {decision.type_decision} dans l'état actuel des autres compétences."
        )
    precision = ""
    if autre.type_decision == "sondage":
        precision = " Cette compétence resterait peu observée."
    return (
        f"Si « {nom} » était déjà consolidée (0,85), la proposition deviendrait "
        f"« {autre.type_decision} », centrée sur « {libelle(autre.competence_focale)} »."
        f"{precision}"
    )


def _constats(etat: EtatApprenant, decision: DecisionAdaptation) -> tuple[str, ...]:
    code = decision.competence_focale
    lignes = [
        (
            f"{libelle(code)} : maîtrise autonome {_fmt(etat.maitrise(code))}, "
            f"incertitude {_fmt(etat.incertitude(code))}, "
            f"{_fmt(etat.preuves(code))} observations équivalentes, "
            f"{_qualite_tendance(etat.vitesse(code))}."
        ),
        (
            f"Le canal assisté de cette compétence est à {_fmt(etat.maitrise_assistee(code))}. "
            "Les réussites avec aide y sont consignées à part."
        ),
    ]
    if etat.journal:
        dernier = etat.journal[-1]
        responsable = max(dernier.responsabilites, key=dernier.responsabilites.get)
        issue = "réussite" if dernier.reussite else "réponse non réussie"
        lignes.append(
            (
                f"Dernière {issue} ({dernier.identifiant_item}) : réussite estimée avant mise à jour "
                f"{_fmt(dernier.probabilite_estimee)}. La révision la plus importante porte sur "
                f"« {libelle(responsable)} »."
            )
        )
    return tuple(lignes)


def _raisons(decision: DecisionAdaptation) -> tuple[str, ...]:
    raisons = [REGLES[regle] for regle in decision.regles]
    parts = ", ".join(
        f"{libelle(code)} {_fmt(part)}"
        for code, part in sorted(decision.repartition.items(), key=lambda item: -item[1])
    )
    raisons.append(
        f"Répartition visée des processus : {parts}. "
        f"Texte de bande {decision.bande_linguistique}, demande cognitive {_fmt(decision.demande_cognitive)}."
    )
    raisons.append(
        f"Sans étayage, la réussite focale estimée est {_fmt(decision.probabilite_sans_etayage)} ; "
        f"avec l'étayage retenu, elle est {_fmt(decision.probabilite_avec_etayage)}."
    )
    return tuple(raisons)


def _texte_enseignant(
    etat: EtatApprenant,
    decision: DecisionAdaptation,
    constats: tuple[str, ...],
    raisons: tuple[str, ...],
    limites: tuple[str, ...],
    contrefactuel: str,
) -> str:
    nom = libelle(decision.competence_focale)
    alternatives = [
        libelle(ligne.code)
        for ligne in decision.priorites
        if ligne.code != decision.competence_focale
    ][:2]
    alternative = ""
    if alternatives:
        alternative = (
            " Autres priorités calculées, à confirmer si elles ont encore peu d'observations : "
            + " ; ".join(alternatives)
            + "."
        )
    paragraphes = [
        (
            f"Proposition pour {etat.profil.identifiant} ({etat.profil.niveau}) : "
            f"{decision.type_decision} centrée sur « {nom} »."
            f"{alternative}"
        ),
        "Constats",
        *[f"- {ligne}" for ligne in constats],
        "Règles appliquées",
        *[f"- {ligne}" for ligne in raisons],
        "Limites",
        *[f"- {ligne}" for ligne in limites],
        "Contrefactuel",
        f"- {contrefactuel}",
        "L'enseignant valide, ajuste ou écarte cette proposition avant de la proposer à l'élève.",
    ]
    return "\n".join(paragraphes)


def _texte_eleve(decision: DecisionAdaptation) -> str:
    gestes = {
        "INF": "Aujourd'hui, plusieurs questions demandent de comprendre un lien que le texte suggère.",
        "EXP": "Aujourd'hui, tu vas retrouver des informations écrites dans le texte.",
        "COH": "Aujourd'hui, tu vas suivre de qui ou de quoi parle le texte d'une phrase à l'autre.",
        "MAC": "Aujourd'hui, tu vas dire de quoi parle le texte dans son ensemble.",
        "EVA": "Aujourd'hui, tu vas dire quelle phrase du texte soutient ta réponse.",
        "VOC": "Aujourd'hui, tu vas t'appuyer sur la phrase pour comprendre un mot.",
        "FLU": "Aujourd'hui, tu vas relire un court passage à voix haute, tranquillement.",
        "DEC": "Aujourd'hui, tu vas prendre le temps de reconnaître les mots du texte.",
        "SYN": "Aujourd'hui, tu vas dire qui fait l'action dans la phrase.",
        "STR": "Aujourd'hui, tu vas choisir l'indice du texte qui t'a aidé.",
        "REG": "Aujourd'hui, tu pourras dire si tu es sûr, un peu sûr, ou pas sûr de ta réponse.",
    }
    outils = {
        "aucun": "Tu peux relire la phrase avant de répondre.",
        "rappel_strategie": "Un outil : cherche ce que le texte permet de comprendre, même si ce n'est pas écrit mot à mot.",
        "segmentation": "Un outil : avance phrase par phrase.",
        "connecteurs": "Un outil : les mots quand, parce que, alors, donc, mais et pour montrent un lien.",
        "modelage": "On cherchera ensemble l'indice de la première question, puis tu continueras.",
    }
    if decision.type_decision == "regulation":
        entree = "On commence par un texte court et des questions dont la réponse est écrite dans le texte."
    elif decision.type_decision == "sondage":
        entree = "Ce sont quelques questions variées pour voir comment tu t'y prends aujourd'hui."
    else:
        entree = gestes[decision.competence_focale]
    return " ".join(
        (
            entree,
            outils[decision.etayage],
            "Si tu hésites, tu peux relire. Chercher un indice fait partie du travail.",
        )
    )


def _texte_famille(etat: EtatApprenant, decision: DecisionAdaptation) -> str:
    nom = libelle(decision.competence_focale).lower()
    return (
        f"L'activité prévue en {etat.profil.niveau} fait travailler « {nom} ». "
        "Elle s'appuie sur ce que l'élève sait déjà faire dans les textes et propose un pas supplémentaire. "
        "L'enseignant peut accompagner la recherche des indices. "
        "Cette indication décrit une étape de travail ; elle ne classe pas l'élève et ne le compare pas aux autres."
    )


def construire_explication(
    etat: EtatApprenant,
    decision: DecisionAdaptation,
    indicateurs: IndicateursSeance,
    public: str = "enseignant",
) -> Explication:
    if public not in PUBLICS:
        raise ValueError(f"Public inconnu : {public}")
    constats = _constats(etat, decision)
    raisons = _raisons(decision)
    limites = decision.mises_en_garde
    contrefactuel = _contrefactuel(etat, decision, indicateurs)
    if public == "enseignant":
        texte = _texte_enseignant(etat, decision, constats, raisons, limites, contrefactuel)
        resume = texte.split("\n", 1)[0]
    elif public == "eleve":
        texte = _texte_eleve(decision)
        resume = texte
        constats = ()
        raisons = ()
        limites = ()
        contrefactuel = ""
    else:
        texte = _texte_famille(etat, decision)
        resume = texte
        constats = ()
        raisons = (
            "Le détail des estimations reste un outil professionnel de l'enseignant.",
        )
        limites = (
            "Ce message décrit l'activité du jour, sans profil chiffré.",
        )
        contrefactuel = ""
    return Explication(
        public=public,
        resume=resume,
        constats=constats,
        raisons=raisons,
        limites=limites,
        contrefactuels=(contrefactuel,) if contrefactuel else (),
        texte=texte,
    )
