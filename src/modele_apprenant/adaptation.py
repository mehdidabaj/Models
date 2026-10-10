"""Politique d'adaptation lexicographique et explicable.

L'ordre des règles est stable : régulation de l'engagement de séance,
enrichissement, sondage tant que l'évidence manque, sinon consolidation
dans la zone proximale. La bande linguistique du texte et la demande
cognitive des questions sont choisies séparément. L'étayage retenu est
le plus léger qui place la réussite estimée au-dessus du seuil visé.
"""

from __future__ import annotations

from dataclasses import dataclass

from modele_apprenant.analytique import IndicateursSeance
from modele_apprenant.constantes import (
    CIBLE_REUSSITE,
    FACTEUR_HORS_ZONE,
    INCERTITUDE_A_SIGNALER,
    INCERTITUDE_CONSOLIDATION_MAX,
    PENALITE_PREREQUIS,
    PLANCHER_FIABILITE,
    PREUVES_CONSOLIDATION,
    PREUVES_SONDAGE,
    SEUIL_PREREQUIS,
    SEUIL_PREUVES_BLOCAGE,
    SEUILS_BANDE,
    TAILLE_SEANCE_ENGAGEMENT,
    TAUX_ABANDON_REGULATION,
    TAUX_HATIF_REGULATION,
    TAUX_REUSSITE_REGULATION,
    ZONE_PROXIMALE,
)
from modele_apprenant.etat import EtatApprenant
from modele_apprenant.inference import probabilite_reussite
from modele_apprenant.ontologie import (
    COMPETENCES_CENTRALES,
    ETAYAGES,
    ORDRE,
    PREREQUIS,
    attendu,
    poids_didactique,
)


@dataclass(frozen=True)
class Priorite:
    code: str
    score: float
    ecart: float
    bloquee: bool
    bloquants: tuple[str, ...]


@dataclass(frozen=True)
class DecisionAdaptation:
    type_decision: str
    competence_focale: str
    competences_concernees: tuple[str, ...]
    regles: tuple[str, ...]
    bande_linguistique: int
    demande_cognitive: float
    difficulte_linguistique: float
    repartition: dict[str, float]
    etayage: str
    probabilite_sans_etayage: float
    probabilite_avec_etayage: float
    nombre_items: int
    duree_minutes: int
    theme: str | None
    priorites: tuple[Priorite, ...]
    mises_en_garde: tuple[str, ...]
    validation_enseignante: bool = True


def regulation_engagee(indicateurs: IndicateursSeance) -> bool:
    if indicateurs.nombre < TAILLE_SEANCE_ENGAGEMENT:
        return False
    reponses_hatives = (
        indicateurs.taux_hatif >= TAUX_HATIF_REGULATION
        and indicateurs.taux_reussite <= TAUX_REUSSITE_REGULATION
    )
    return reponses_hatives or indicateurs.taux_abandon >= TAUX_ABANDON_REGULATION


def prerequis_insuffisants(etat: EtatApprenant, code: str) -> tuple[str, ...]:
    bloquants = []
    for prerequis in PREREQUIS.get(code, ()):
        if (
            etat.preuves(prerequis) >= SEUIL_PREUVES_BLOCAGE
            and etat.maitrise(prerequis) < SEUIL_PREREQUIS
        ):
            bloquants.append(prerequis)
    return tuple(bloquants)


def _facteur_zone(maitrise: float) -> float:
    bas, haut = ZONE_PROXIMALE
    if bas <= maitrise <= haut:
        return 1.0
    return FACTEUR_HORS_ZONE


def calculer_priorites(etat: EtatApprenant) -> tuple[Priorite, ...]:
    niveau = etat.profil.niveau
    lignes = []
    for code in ORDRE:
        maitrise = etat.maitrise(code)
        ecart = max(0.0, attendu(niveau, code) - maitrise)
        bloquants = prerequis_insuffisants(etat, code)
        fiabilite = PLANCHER_FIABILITE + (1.0 - PLANCHER_FIABILITE) * etat.fiabilite(code)
        penalite = PENALITE_PREREQUIS if bloquants else 1.0
        score = ecart * _facteur_zone(maitrise) * fiabilite * poids_didactique(niveau, code) * penalite
        lignes.append(Priorite(code, score, ecart, bool(bloquants), bloquants))
    lignes.sort(key=lambda ligne: (-ligne.score, ORDRE.index(ligne.code)))
    return tuple(lignes)


def est_consolide(etat: EtatApprenant) -> bool:
    return all(
        etat.maitrise(code) >= attendu(etat.profil.niveau, code)
        and etat.incertitude(code) <= INCERTITUDE_CONSOLIDATION_MAX
        and etat.preuves(code) >= PREUVES_CONSOLIDATION
        for code in COMPETENCES_CENTRALES
    )


def bande_linguistique(score: float) -> int:
    return 1 + sum(score >= seuil for seuil in SEUILS_BANDE)


def demande_pour(maitrise: float) -> float:
    if maitrise < 0.40:
        return 0.30
    if maitrise < 0.55:
        return 0.42
    if maitrise < 0.70:
        return 0.55
    return 0.68


def _normaliser(parts: dict[str, float]) -> dict[str, float]:
    total = sum(parts.values())
    return {code: valeur / total for code, valeur in parts.items() if valeur > 0}


def _repartition(
    etat: EtatApprenant,
    type_decision: str,
    focus: str,
    concernees: tuple[str, ...],
) -> dict[str, float]:
    if type_decision == "sondage":
        return _normaliser({code: 1.0 for code in concernees})
    if type_decision == "regulation":
        parts = {focus: 0.35, "EXP": 0.50, "VOC": 0.15}
        return _normaliser(parts)
    if type_decision == "enrichissement":
        return {"EVA": 0.40, "MAC": 0.35, "INF": 0.25}
    parts = {focus: 0.50, "EXP": 0.25}
    prerequis = PREREQUIS.get(focus, ())
    if prerequis:
        plus_fragile = min(prerequis, key=lambda code: (etat.maitrise(code), ORDRE.index(code)))
        parts[plus_fragile] = parts.get(plus_fragile, 0.0) + 0.15
    else:
        parts["VOC"] = parts.get("VOC", 0.0) + 0.15
    prolongement = {"INF": "MAC", "EXP": "INF", "MAC": "EVA", "COH": "INF", "VOC": "INF"}.get(focus)
    if prolongement:
        parts[prolongement] = parts.get(prolongement, 0.0) + 0.10
    else:
        parts[focus] += 0.10
    return _normaliser(parts)


def _competences_sondees(focus: str, priorites: tuple[Priorite, ...]) -> tuple[str, ...]:
    retenues: list[str] = []
    for code in (focus, "EXP", *(ligne.code for ligne in priorites)):
        if code not in retenues:
            retenues.append(code)
        if len(retenues) == 3:
            break
    return tuple(retenues)


def choisir_etayage(
    etat: EtatApprenant,
    focus: str,
    demande: float,
    difficulte_linguistique: float,
    forcer_aucun: bool,
    interdire_modelage: bool = False,
) -> tuple[str, float, float]:
    options = [
        etayage
        for etayage in ETAYAGES[focus]
        if not (interdire_modelage and etayage == "modelage")
    ]
    if etat.profil.consigne_accessible and "segmentation" not in options:
        options.insert(1, "segmentation")
    if not options:
        options = ["aucun"]
    probabilite_nue = probabilite_reussite(
        etat, (focus,), demande, difficulte_linguistique, "aucun", focus
    )
    if forcer_aucun:
        return "aucun", probabilite_nue, probabilite_nue
    choisi = options[0]
    probabilite = probabilite_nue
    for etayage in options:
        probabilite = probabilite_reussite(
            etat, (focus,), demande, difficulte_linguistique, etayage, focus
        )
        choisi = etayage
        if probabilite >= CIBLE_REUSSITE:
            break
    return choisi, probabilite_nue, probabilite


def decider(etat: EtatApprenant, indicateurs: IndicateursSeance) -> DecisionAdaptation:
    priorites = calculer_priorites(etat)
    focus = priorites[0].code
    regles: list[str] = []
    bloquants = prerequis_insuffisants(etat, focus)
    if bloquants:
        focus = min(bloquants, key=lambda code: (etat.maitrise(code), ORDRE.index(code)))
        regles.append("R5_RETOUR_PREREQUIS")

    if regulation_engagee(indicateurs):
        type_decision = "regulation"
        regles.append("R1_REGULATION_ENGAGEMENT")
        concernees = (focus, "EXP", "VOC")
    elif est_consolide(etat):
        type_decision = "enrichissement"
        regles.append("R3_ENRICHISSEMENT")
        focus = "EVA" if etat.maitrise("EVA") < attendu(etat.profil.niveau, "EVA") else "MAC"
        concernees = ("EVA", "MAC", "INF")
    elif etat.preuves(focus) < PREUVES_SONDAGE:
        type_decision = "sondage"
        regles.append("R2_SONDAGE_INCERTITUDE")
        concernees = _competences_sondees(focus, priorites)
        if "EXP" in concernees:
            regles.append("R10_ANCRE_EXPLICITE")
    else:
        type_decision = "consolidation"
        regles.append("R4_CONSOLIDATION_ZPD")
        concernees = (focus,)

    score = etat.score_linguistique()
    bande = bande_linguistique(score)
    difficulte = score
    if (
        type_decision == "enrichissement"
        and not etat.profil.consigne_accessible
        and etat.maitrise("FLU") >= 0.65
        and etat.maitrise("DEC") >= 0.70
    ):
        bande = min(5, bande + 1)
        difficulte = min(0.95, score + 0.10)
    regles.append("R7_BANDE_LINGUISTIQUE")

    if type_decision == "enrichissement":
        demande = 0.72
    elif type_decision == "sondage":
        demande = 0.40
    else:
        demande = demande_pour(etat.maitrise(focus))
    regles.append("R8_DEMANDE_COGNITIVE")

    forcer_aucun = type_decision == "sondage"
    etayage, p_sans, p_avec = choisir_etayage(
        etat,
        focus,
        demande,
        difficulte,
        forcer_aucun,
        interdire_modelage=type_decision == "regulation",
    )
    regles.append("R6_ETAYAGE_MINIMAL")
    regles.append("R9_VALIDATION_ENSEIGNANTE")

    if type_decision == "sondage":
        nombre, duree = 6, 10
    elif type_decision == "regulation":
        nombre, duree = 4, 8
    elif type_decision == "enrichissement":
        nombre, duree = 6, 15
    else:
        nombre, duree = 8, 15

    gardes: list[str] = []
    if etat.incertitude(focus) >= INCERTITUDE_A_SIGNALER:
        gardes.append(
            "L'estimation de la compétence focale reste incertaine et se précisera avec de nouvelles observations."
        )
    if etayage == "modelage":
        gardes.append(
            "La réussite attendue sous modelage relève du canal assisté. Elle ne sera pas lue comme une maîtrise autonome."
        )
    if p_avec < CIBLE_REUSSITE:
        gardes.append(
            "Même l'étayage le plus engagé laisse la réussite estimée sous la zone visée. L'enseignant peut raccourcir encore la tâche ou revenir à un prérequis."
        )
    if type_decision == "sondage":
        gardes.append(
            "Le sondage est proposé sans étayage afin d'observer la réussite autonome."
        )
    themes = etat.profil.themes
    theme = themes[0] if themes else None

    return DecisionAdaptation(
        type_decision=type_decision,
        competence_focale=focus,
        competences_concernees=concernees,
        regles=tuple(regles),
        bande_linguistique=bande,
        demande_cognitive=demande,
        difficulte_linguistique=difficulte,
        repartition=_repartition(etat, type_decision, focus, concernees),
        etayage=etayage,
        probabilite_sans_etayage=p_sans,
        probabilite_avec_etayage=p_avec,
        nombre_items=nombre,
        duree_minutes=duree,
        theme=theme,
        priorites=priorites,
        mises_en_garde=tuple(gardes),
    )
