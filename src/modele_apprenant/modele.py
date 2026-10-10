"""Façade du modèle de l'apprenant.

Le diagnostic reste dans le modèle symbolique. La génération rend une
spécification déjà décidée. L'enseignant valide avant la passation.
"""

from __future__ import annotations

from modele_apprenant.adaptation import DecisionAdaptation, decider
from modele_apprenant.analytique import IndicateursSeance, calculer_indicateurs, profil_ouvert
from modele_apprenant.etat import EtatApprenant
from modele_apprenant.explication import Explication, construire_explication
from modele_apprenant.generation import (
    Activite,
    GenerateurParGabarits,
    SpecificationActivite,
    construire_specification,
    valider_activite,
)
from modele_apprenant.inference import integrer_trace
from modele_apprenant.traces import ProfilApprenant, TraceReponse


class ModeleApprenant:
    def __init__(self, generateur: GenerateurParGabarits | None = None) -> None:
        self.generateur = generateur or GenerateurParGabarits()

    def initialiser(self, profil: ProfilApprenant) -> EtatApprenant:
        return EtatApprenant.initial(profil)

    def observer(self, etat: EtatApprenant, trace: TraceReponse) -> EtatApprenant:
        integrer_trace(etat, trace)
        return etat

    def indicateurs(self, etat: EtatApprenant) -> IndicateursSeance:
        return calculer_indicateurs(etat.traces_seance)

    def proposer(self, etat: EtatApprenant) -> DecisionAdaptation:
        return decider(etat, self.indicateurs(etat))

    def expliquer(
        self,
        etat: EtatApprenant,
        decision: DecisionAdaptation | None = None,
        public: str = "enseignant",
    ) -> Explication:
        decision = decision or self.proposer(etat)
        return construire_explication(etat, decision, self.indicateurs(etat), public)

    def specifier(
        self,
        etat: EtatApprenant,
        decision: DecisionAdaptation | None = None,
    ) -> SpecificationActivite:
        decision = decision or self.proposer(etat)
        return construire_specification(etat, decision)

    def generer(self, specification: SpecificationActivite) -> Activite:
        activite = self.generateur.generer(specification)
        alertes = valider_activite(activite, specification)
        activite.alertes_validation = alertes
        if alertes:
            activite.note_enseignant = (
                "Activité à revoir avant passation. "
                + " ".join(alertes)
                + " "
                + activite.note_enseignant
            )
        return activite

    def profil(self, etat: EtatApprenant) -> list[dict[str, float | str]]:
        return profil_ouvert(etat)
