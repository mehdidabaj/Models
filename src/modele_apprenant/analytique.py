"""Indicateurs de learning analytics calculés sur la séance en cours.

Ces indicateurs décrivent un comportement de réponse observé. Ils ne sont
pas stockés comme des traits durables de l'élève.
"""

from __future__ import annotations

from dataclasses import dataclass

from modele_apprenant.constantes import SEUIL_REPONSE_HATIVE_MS
from modele_apprenant.etat import EtatApprenant
from modele_apprenant.ontologie import ORDRE, libelle
from modele_apprenant.traces import TraceReponse


@dataclass(frozen=True)
class IndicateursSeance:
    nombre: int
    taux_reussite: float
    taux_hatif: float
    taux_aides: float
    taux_abandon: float
    taux_relecture: float
    ecart_calibration: float | None

    @staticmethod
    def vide() -> IndicateursSeance:
        return IndicateursSeance(0, 0.0, 0.0, 0.0, 0.0, 0.0, None)


def calculer_indicateurs(traces: list[TraceReponse]) -> IndicateursSeance:
    nombre = len(traces)
    if nombre == 0:
        return IndicateursSeance.vide()
    reussites = sum(1 for trace in traces if trace.reussite and not trace.abandon)
    hatives = sum(
        1
        for trace in traces
        if trace.temps_ms is not None and trace.temps_ms < SEUIL_REPONSE_HATIVE_MS
    )
    aides = sum(1 for trace in traces if trace.aides_utilisees > 0)
    abandons = sum(1 for trace in traces if trace.abandon)
    relectures = sum(1 for trace in traces if trace.relectures > 0)
    ecarts = [
        abs(trace.confiance - (1.0 if trace.reussite else 0.0))
        for trace in traces
        if trace.confiance is not None
    ]
    calibration = sum(ecarts) / len(ecarts) if ecarts else None
    return IndicateursSeance(
        nombre=nombre,
        taux_reussite=reussites / nombre,
        taux_hatif=hatives / nombre,
        taux_aides=aides / nombre,
        taux_abandon=abandons / nombre,
        taux_relecture=relectures / nombre,
        ecart_calibration=calibration,
    )


def profil_ouvert(etat: EtatApprenant) -> list[dict[str, float | str]]:
    """Profil lisible pour un modèle ouvert de l'apprenant, côté enseignant."""
    lignes = []
    for code in ORDRE:
        lignes.append(
            {
                "code": code,
                "libelle": libelle(code),
                "maitrise_autonome": round(etat.maitrise(code), 4),
                "maitrise_assistee": round(etat.maitrise_assistee(code), 4),
                "incertitude": round(etat.incertitude(code), 4),
                "preuves": round(etat.preuves(code), 4),
                "vitesse": round(etat.vitesse(code), 4),
            }
        )
    return lignes
