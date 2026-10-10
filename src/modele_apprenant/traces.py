"""Traces d'apprentissage minimales.

Le schéma retient ce qui éclaire la compréhension et l'adaptation.
Il exclut les attributs sensibles : pas de diagnostic, pas de situation
familiale, pas de comparaison entre élèves.
"""

from __future__ import annotations

from dataclasses import dataclass

from modele_apprenant.ontologie import COMPETENCES, NIVEAUX


@dataclass(frozen=True)
class TraceReponse:
    """Une réponse observée, déjà reliée à sa matrice Q.

    `competences` est la ligne de la matrice Q : les compétences que l'item
    demande vraiment. `processus` est l'étiquette didactique principale,
    utilisée pour l'étayage et le bilan de séance.
    """

    identifiant_item: str
    competences: tuple[str, ...]
    processus: str
    reussite: bool
    difficulte_cognitive: float = 0.5
    difficulte_linguistique: float = 0.5
    temps_ms: int | None = None
    aides_utilisees: int = 0
    relectures: int = 0
    confiance: float | None = None
    abandon: bool = False
    moment: float = 0.0
    seance: str = "seance-1"

    def __post_init__(self) -> None:
        if not self.identifiant_item:
            raise ValueError("L'item doit porter un identifiant.")
        if not self.seance:
            raise ValueError("La séance doit porter un identifiant.")
        if not self.competences:
            raise ValueError("La matrice Q de l'item est vide.")
        if len(set(self.competences)) != len(self.competences):
            raise ValueError("La matrice Q contient un doublon.")
        inconnues = [c for c in self.competences if c not in COMPETENCES]
        if inconnues:
            raise ValueError(f"Compétences inconnues : {inconnues}")
        if self.processus not in COMPETENCES:
            raise ValueError(f"Processus inconnu : {self.processus}")
        for nom, valeur in (
            ("difficulte_cognitive", self.difficulte_cognitive),
            ("difficulte_linguistique", self.difficulte_linguistique),
        ):
            if not 0.0 <= valeur <= 1.0:
                raise ValueError(f"{nom} doit être compris entre 0 et 1.")
        if self.temps_ms is not None and self.temps_ms < 0:
            raise ValueError("Le temps de réponse est négatif.")
        if self.aides_utilisees < 0 or self.relectures < 0:
            raise ValueError("Les aides et les relectures sont des comptes positifs.")
        if self.confiance is not None and not 0.0 <= self.confiance <= 1.0:
            raise ValueError("La confiance doit être comprise entre 0 et 1.")
        if self.moment < 0:
            raise ValueError("Le moment est exprimé en jours positifs.")


@dataclass(frozen=True)
class ProfilApprenant:
    """Profil opératoire minimal, saisi ou confirmé par l'enseignant.

    L'identifiant est un pseudonyme. Les aménagements sont des choix
    professionnels ; le modèle ne les infère pas.
    """

    identifiant: str
    niveau: str
    themes: tuple[str, ...] = ()
    consigne_accessible: bool = False
    lecture_adulte_possible: bool = False

    def __post_init__(self) -> None:
        if not self.identifiant or " " in self.identifiant or "@" in self.identifiant:
            raise ValueError(
                "L'identifiant doit être un pseudonyme, sans espace et sans adresse."
            )
        if self.niveau not in NIVEAUX:
            raise ValueError(f"Niveau inconnu : {self.niveau}")
