"""État dynamique de l'apprenant.

Chaque compétence porte deux canaux Beta-Bernoulli :
- autonome : réussite sans aide ;
- assisté : réussite obtenue avec un étayage.

L'écoulement dans le temps rapproche les comptes du prior de niveau et
augmente ainsi l'incertitude lorsqu'aucune nouvelle trace n'arrive.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field

from modele_apprenant.constantes import (
    LAMBDA_ECOULEMENT,
    RHO_VITESSE,
    VERSION_MODELE,
)
from modele_apprenant.ontologie import (
    ORDRE,
    POIDS_LINGUISTIQUES,
    beta_initiale,
    libelle,
)
from modele_apprenant.traces import ProfilApprenant, TraceReponse


@dataclass
class CanalCompetence:
    alpha: float
    beta: float
    alpha0: float
    beta0: float
    preuves: float = 0.0
    vitesse: float = 0.0

    def maitrise(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def appliquer(self, masse: float, reussite: bool, memoriser_vitesse: bool) -> float:
        if masse <= 0:
            return 0.0
        avant = self.maitrise()
        if reussite:
            self.alpha += masse
        else:
            self.beta += masse
        self.preuves += masse
        delta = self.maitrise() - avant
        if memoriser_vitesse:
            self.vitesse = (1.0 - RHO_VITESSE) * self.vitesse + RHO_VITESSE * delta
        return delta

    def ecouler(self, retenue: float) -> None:
        self.alpha = self.alpha0 + (self.alpha - self.alpha0) * retenue
        self.beta = self.beta0 + (self.beta - self.beta0) * retenue
        self.preuves *= retenue
        self.vitesse *= retenue

    def ecart_type(self) -> float:
        total = self.alpha + self.beta
        variance = (self.alpha * self.beta) / (total * total * (total + 1.0))
        return math.sqrt(variance)


@dataclass(frozen=True)
class JournalMiseAJour:
    identifiant_item: str
    reussite: bool
    probabilite_estimee: float
    facteur_surprise: float
    qualite: float
    responsabilites: dict[str, float]
    deltas: dict[str, float]


@dataclass
class EtatApprenant:
    profil: ProfilApprenant
    autonome: dict[str, CanalCompetence]
    assiste: dict[str, CanalCompetence]
    moment: float = 0.0
    seance_id: str | None = None
    traces_seance: list[TraceReponse] = field(default_factory=list)
    journal: list[JournalMiseAJour] = field(default_factory=list)

    @classmethod
    def initial(cls, profil: ProfilApprenant) -> EtatApprenant:
        autonome: dict[str, CanalCompetence] = {}
        assiste: dict[str, CanalCompetence] = {}
        for code in ORDRE:
            alpha, beta = beta_initiale(profil.niveau, code)
            autonome[code] = CanalCompetence(alpha, beta, alpha, beta)
            assiste[code] = CanalCompetence(alpha, beta, alpha, beta)
        return cls(profil=profil, autonome=autonome, assiste=assiste)

    def maitrise(self, code: str) -> float:
        return self.autonome[code].maitrise()

    def maitrise_assistee(self, code: str) -> float:
        return self.assiste[code].maitrise()

    def preuves(self, code: str) -> float:
        return self.autonome[code].preuves

    def incertitude(self, code: str) -> float:
        reference = math.sqrt(1.0 / 12.0)
        return min(1.0, self.autonome[code].ecart_type() / reference)

    def fiabilite(self, code: str) -> float:
        return 1.0 - self.incertitude(code)

    def vitesse(self, code: str) -> float:
        return self.autonome[code].vitesse

    def score_linguistique(self) -> float:
        return sum(
            poids * self.maitrise(code) for code, poids in POIDS_LINGUISTIQUES.items()
        )

    def copier(self) -> EtatApprenant:
        return copy.deepcopy(self)

    def fixer_maitrise(self, code: str, maitrise: float, preuves: float | None = None) -> None:
        canal = self.autonome[code]
        if preuves is not None:
            canal.preuves = max(0.0, preuves)
        total = canal.alpha0 + canal.beta0 + canal.preuves
        valeur = min(max(maitrise, 0.02), 0.98)
        canal.alpha = valeur * total
        canal.beta = (1.0 - valeur) * total

    def ecouler_jusqua(self, moment: float) -> None:
        if moment < self.moment - 1e-9:
            raise ValueError("Une trace antérieure au dernier moment connu a été reçue.")
        delta = moment - self.moment
        if delta <= 0:
            self.moment = moment
            return
        retenue = math.exp(-LAMBDA_ECOULEMENT * delta)
        for code in ORDRE:
            self.autonome[code].ecouler(retenue)
            self.assiste[code].ecouler(retenue)
        self.moment = moment

    def ouvrir_seance(self, seance: str) -> None:
        if self.seance_id != seance:
            self.traces_seance = []
            self.seance_id = seance

    def vers_dict(self) -> dict:
        competences = []
        for code in ORDRE:
            competences.append(
                {
                    "code": code,
                    "libelle": libelle(code),
                    "maitrise_autonome": round(self.maitrise(code), 4),
                    "maitrise_assistee": round(self.maitrise_assistee(code), 4),
                    "incertitude": round(self.incertitude(code), 4),
                    "preuves_autonomes": round(self.preuves(code), 4),
                    "preuves_assistees": round(self.assiste[code].preuves, 4),
                    "vitesse": round(self.vitesse(code), 4),
                }
            )
        return {
            "version_modele": VERSION_MODELE,
            "identifiant": self.profil.identifiant,
            "niveau": self.profil.niveau,
            "moment": self.moment,
            "score_linguistique": round(self.score_linguistique(), 4),
            "competences": competences,
        }
