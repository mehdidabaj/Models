"""Scénario illustratif : un élève de CE2 qui prélève l'explicite et consolide encore les inférences.

Le scénario montre le comportement du modèle. Il ne constitue pas un résultat
empirique sur des élèves réels.
"""

from __future__ import annotations

from dataclasses import dataclass

from modele_apprenant.adaptation import DecisionAdaptation
from modele_apprenant.etat import EtatApprenant
from modele_apprenant.explication import Explication
from modele_apprenant.generation import Activite
from modele_apprenant.modele import ModeleApprenant
from modele_apprenant.traces import ProfilApprenant, TraceReponse


@dataclass(frozen=True)
class ResultatSimulation:
    etat: EtatApprenant
    decision: DecisionAdaptation
    explication_enseignant: Explication
    explication_eleve: Explication
    explication_famille: Explication
    activite: Activite


def simulation_ce2() -> ResultatSimulation:
    modele = ModeleApprenant()
    etat = modele.initialiser(
        ProfilApprenant("eleve-ce2-01", "CE2", themes=("animaux",))
    )
    for index in range(4):
        modele.observer(
            etat,
            TraceReponse(
                identifiant_item=f"exp-{index}",
                competences=("EXP",),
                processus="EXP",
                reussite=True,
                temps_ms=25000,
                difficulte_cognitive=0.45,
                difficulte_linguistique=0.52,
                moment=0.0,
                seance="seance-1",
            ),
        )
    for index in range(4):
        modele.observer(
            etat,
            TraceReponse(
                identifiant_item=f"inf-{index}",
                competences=("INF",),
                processus="INF",
                reussite=False,
                temps_ms=32000,
                relectures=1 if index == 0 else 0,
                difficulte_cognitive=0.55,
                difficulte_linguistique=0.52,
                moment=0.0,
                seance="seance-1",
            ),
        )
    decision = modele.proposer(etat)
    return ResultatSimulation(
        etat=etat,
        decision=decision,
        explication_enseignant=modele.expliquer(etat, decision, "enseignant"),
        explication_eleve=modele.expliquer(etat, decision, "eleve"),
        explication_famille=modele.expliquer(etat, decision, "famille"),
        activite=modele.generer(modele.specifier(etat, decision)),
    )


def formater_rapport(resultat: ResultatSimulation) -> str:
    etat = resultat.etat
    decision = resultat.decision
    lignes = [
        "Scénario CE2 — prélèvement réussi, inférences encore incertaines",
        "",
        (
            f"Prélèvement explicite : {etat.maitrise('EXP'):.2f} "
            f"(assisté {etat.maitrise_assistee('EXP'):.2f})"
        ),
        (
            f"Inférences : {etat.maitrise('INF'):.2f} "
            f"(assisté {etat.maitrise_assistee('INF'):.2f})"
        ),
        (
            f"Décision : {decision.type_decision} / {decision.competence_focale} / "
            f"bande {decision.bande_linguistique} / étayage {decision.etayage}"
        ),
        f"Règles : {', '.join(decision.regles)}",
        "",
        "Explication enseignant",
        resultat.explication_enseignant.texte,
        "",
        "Message élève",
        resultat.explication_eleve.texte,
        "",
        "Message famille",
        resultat.explication_famille.texte,
        "",
        "Activité",
        resultat.activite.texte_eleve(),
        "",
        f"Alertes de validation : {resultat.activite.alertes_validation or 'aucune'}",
    ]
    return "\n".join(lignes)
