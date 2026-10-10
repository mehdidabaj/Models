"""Modèle intelligent, dynamique et explicable de l'apprenant en compréhension écrite."""

from modele_apprenant.constantes import VERSION_MODELE
from modele_apprenant.modele import ModeleApprenant
from modele_apprenant.traces import ProfilApprenant, TraceReponse

__all__ = [
    "VERSION_MODELE",
    "ModeleApprenant",
    "ProfilApprenant",
    "TraceReponse",
]
__version__ = VERSION_MODELE
