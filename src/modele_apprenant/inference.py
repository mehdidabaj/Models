"""Mise à jour explicable de l'état.

Une observation est d'abord pondérée par sa qualité (abandon, réponse trop
rapide, aide). Sa masse est ensuite répartie entre les compétences de la
matrice Q selon la responsabilité : en cas de réussite, les compétences
déjà solides reçoivent davantage de crédit ; en cas d'erreur, les
compétences les plus fragiles reçoivent davantage de la révision.

Le modulateur de surprise augmente le poids d'une réponse peu attendue.
Le canal assisté reçoit la réussite obtenue avec aide, sans la faire passer
pour une maîtrise autonome.
"""

from __future__ import annotations

import math

from modele_apprenant.constantes import (
    BIAIS_REUSSITE,
    ECART_CALIBRATION_LARGE,
    ECART_CALIBRATION_SERRE,
    EFFETS_ETAYAGE,
    MASSE_CALIBRATION,
    MASSE_CALIBRATION_JUSTE,
    MASSE_RELECTURE_REG,
    MASSE_RELECTURE_STR,
    PART_ASSISTEE_ECHEC_AIDE,
    PART_ASSISTEE_REUSSITE_AIDEE,
    PART_AUTO_ECHEC_AIDE,
    PART_AUTO_REUSSITE_AIDEE,
    PENTE_SURPRISE,
    PLANCHER_SURPRISE,
    POIDS_ABANDON,
    POIDS_COMPETENCE,
    POIDS_DEMANDE,
    POIDS_ECART_LINGUISTIQUE,
    POIDS_HATIF,
    POIDS_STRATEGIE,
    PROCESSUS_SOUTENUS_PAR_STRATEGIE,
    SEUIL_REPONSE_HATIVE_MS,
    UNITE_EVIDENCE,
)
from modele_apprenant.etat import EtatApprenant, JournalMiseAJour
from modele_apprenant.traces import TraceReponse


def logit(probabilite: float) -> float:
    probabilite = min(max(probabilite, 1e-4), 1.0 - 1e-4)
    return math.log(probabilite / (1.0 - probabilite))


def sigmoide(valeur: float) -> float:
    if valeur >= 0:
        exponentielle = math.exp(-valeur)
        return 1.0 / (1.0 + exponentielle)
    exponentielle = math.exp(valeur)
    return exponentielle / (1.0 + exponentielle)


def effet_etayage(etayage: str, processus: str) -> float:
    if etayage == "aucun":
        return 0.0
    table = EFFETS_ETAYAGE[etayage]
    return table.get(processus, table["*"])


def probabilite_reussite(
    etat: EtatApprenant,
    competences: tuple[str, ...] | list[str],
    demande: float,
    difficulte_linguistique: float,
    etayage: str,
    processus: str,
) -> float:
    if not competences:
        raise ValueError("Le calcul de réussite exige au moins une compétence.")
    moyenne = sum(logit(etat.maitrise(code)) for code in competences) / len(competences)
    lineaire = (
        BIAIS_REUSSITE
        + POIDS_COMPETENCE * moyenne
        - POIDS_DEMANDE * (demande - 0.5)
        - POIDS_ECART_LINGUISTIQUE * (difficulte_linguistique - etat.score_linguistique())
        + effet_etayage(etayage, processus)
    )
    if processus in PROCESSUS_SOUTENUS_PAR_STRATEGIE and "STR" not in competences:
        lineaire += POIDS_STRATEGIE * (etat.maitrise("STR") - 0.5)
    return sigmoide(lineaire)


def qualite_preuve(trace: TraceReponse) -> float:
    qualite = 1.0
    if trace.abandon:
        qualite *= POIDS_ABANDON
    if trace.temps_ms is not None and trace.temps_ms < SEUIL_REPONSE_HATIVE_MS:
        qualite *= POIDS_HATIF
    return qualite


def responsabilites(etat: EtatApprenant, trace: TraceReponse) -> dict[str, float]:
    brut: dict[str, float] = {}
    for code in trace.competences:
        maitrise = etat.maitrise(code)
        if trace.reussite and not trace.abandon:
            brut[code] = 0.25 + 0.75 * maitrise
        else:
            brut[code] = 0.25 + 0.75 * (1.0 - maitrise)
    total = sum(brut.values())
    return {code: valeur / total for code, valeur in brut.items()}


def _masses_canaux(trace: TraceReponse, qualite: float) -> tuple[float, float]:
    unite = UNITE_EVIDENCE * qualite
    if trace.aides_utilisees <= 0:
        return unite, 0.0
    if trace.reussite and not trace.abandon:
        return unite * PART_AUTO_REUSSITE_AIDEE, unite * PART_ASSISTEE_REUSSITE_AIDEE
    return unite * PART_AUTO_ECHEC_AIDE, unite * PART_ASSISTEE_ECHEC_AIDE


def _appliquer_meta(
    etat: EtatApprenant,
    trace: TraceReponse,
    qualite: float,
    deltas: dict[str, float],
) -> None:
    if trace.relectures > 0:
        delta = etat.autonome["REG"].appliquer(MASSE_RELECTURE_REG * qualite, True, True)
        deltas["REG"] = deltas.get("REG", 0.0) + delta
        if trace.reussite and not trace.abandon and trace.aides_utilisees <= 0:
            delta_str = etat.autonome["STR"].appliquer(
                MASSE_RELECTURE_STR * qualite, True, True
            )
            deltas["STR"] = deltas.get("STR", 0.0) + delta_str
    if trace.confiance is None:
        return
    ecart = abs(trace.confiance - (1.0 if trace.reussite and not trace.abandon else 0.0))
    if ecart >= ECART_CALIBRATION_LARGE:
        delta = etat.autonome["REG"].appliquer(MASSE_CALIBRATION * qualite, False, True)
        deltas["REG"] = deltas.get("REG", 0.0) + delta
    elif ecart <= ECART_CALIBRATION_SERRE and not trace.abandon:
        delta = etat.autonome["REG"].appliquer(MASSE_CALIBRATION_JUSTE * qualite, True, True)
        deltas["REG"] = deltas.get("REG", 0.0) + delta


def integrer_trace(etat: EtatApprenant, trace: TraceReponse) -> JournalMiseAJour:
    etat.ecouler_jusqua(trace.moment)
    etat.ouvrir_seance(trace.seance)

    probabilite = probabilite_reussite(
        etat,
        trace.competences,
        trace.difficulte_cognitive,
        trace.difficulte_linguistique,
        "aucun",
        trace.processus,
    )
    surprise = (1.0 - probabilite) if trace.reussite and not trace.abandon else probabilite
    if trace.abandon:
        surprise = probabilite
    facteur = PLANCHER_SURPRISE + PENTE_SURPRISE * surprise
    qualite = qualite_preuve(trace)
    parts = responsabilites(etat, trace)
    masse_auto, masse_aide = _masses_canaux(trace, qualite)
    masse_auto *= facteur
    masse_aide *= facteur
    reussite_effective = trace.reussite and not trace.abandon

    deltas: dict[str, float] = {}
    for code, part in parts.items():
        delta = etat.autonome[code].appliquer(masse_auto * part, reussite_effective, True)
        deltas[code] = deltas.get(code, 0.0) + delta
        if masse_aide > 0:
            etat.assiste[code].appliquer(masse_aide * part, reussite_effective, False)

    _appliquer_meta(etat, trace, qualite, deltas)
    evenement = JournalMiseAJour(
        identifiant_item=trace.identifiant_item,
        reussite=reussite_effective,
        probabilite_estimee=probabilite,
        facteur_surprise=facteur,
        qualite=qualite,
        responsabilites=dict(parts),
        deltas={code: valeur for code, valeur in deltas.items() if abs(valeur) > 1e-12},
    )
    etat.journal.append(evenement)
    if len(etat.journal) > 30:
        del etat.journal[:-30]
    etat.traces_seance.append(trace)
    return evenement
