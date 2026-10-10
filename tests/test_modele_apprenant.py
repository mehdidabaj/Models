"""Tests du modèle de l'apprenant.

Ils vérifient les invariants du modèle, pas une performance sur données réelles.
"""

from __future__ import annotations

import pytest

from modele_apprenant.adaptation import decider
from modele_apprenant.analytique import IndicateursSeance
from modele_apprenant.constantes import KAPPA_PRIOR, MOTS_STIGMATISANTS
from modele_apprenant.demonstration import simulation_ce2
from modele_apprenant.etat import EtatApprenant
from modele_apprenant.generation import (
    Activite,
    QuestionActivite,
    construire_prompt,
    valider_activite,
)
from modele_apprenant.inference import integrer_trace, probabilite_reussite
from modele_apprenant.modele import ModeleApprenant
from modele_apprenant.ontologie import (
    ATTENDU,
    COMPETENCES,
    NIVEAUX,
    ORDRE,
    PREREQUIS,
    PRIOR,
    attendu,
)
from modele_apprenant.traces import ProfilApprenant, TraceReponse


def profil(niveau: str = "CE2", themes: tuple[str, ...] = ()) -> ProfilApprenant:
    return ProfilApprenant(f"eleve-{niveau.lower()}", niveau, themes=themes)


def trace(
    code: str = "EXP",
    *,
    reussite: bool = True,
    temps_ms: int = 20000,
    aides: int = 0,
    relectures: int = 0,
    confiance: float | None = None,
    abandon: bool = False,
    moment: float = 0.0,
    seance: str = "s1",
    identifiant: str = "item",
    competences: tuple[str, ...] | None = None,
    demande: float = 0.5,
) -> TraceReponse:
    return TraceReponse(
        identifiant_item=identifiant,
        competences=competences or (code,),
        processus=code,
        reussite=reussite,
        temps_ms=temps_ms,
        aides_utilisees=aides,
        relectures=relectures,
        confiance=confiance,
        abandon=abandon,
        moment=moment,
        seance=seance,
        difficulte_cognitive=demande,
        difficulte_linguistique=0.5,
    )


def invariant_beta(etat: EtatApprenant) -> None:
    for code in ORDRE:
        for canal in (etat.autonome[code], etat.assiste[code]):
            assert canal.alpha + canal.beta == pytest.approx(
                canal.alpha0 + canal.beta0 + canal.preuves
            )


class TestOntologie:
    def test_referentiel_complet(self) -> None:
        assert set(COMPETENCES) == set(ORDRE)
        for code, prerequis in PREREQUIS.items():
            assert code in COMPETENCES
            assert all(item in COMPETENCES for item in prerequis)
        for niveau in NIVEAUX:
            for code in ORDRE:
                assert 0.0 < PRIOR[niveau][code] < ATTENDU[niveau][code] < 1.0

    def test_pseudonyme(self) -> None:
        with pytest.raises(ValueError):
            ProfilApprenant("Camille Martin", "CE2")
        with pytest.raises(ValueError):
            ProfilApprenant("camille@ecole.fr", "CE1")


class TestMiseAJour:
    def test_reussite_et_echec_deplacent_la_maitrise(self) -> None:
        modele = ModeleApprenant()
        etat = modele.initialiser(profil())
        avant = etat.maitrise("EXP")
        modele.observer(etat, trace("EXP", reussite=True, identifiant="ok"))
        assert etat.maitrise("EXP") > avant
        avant_inf = etat.maitrise("INF")
        modele.observer(etat, trace("INF", reussite=False, identifiant="ko"))
        assert etat.maitrise("INF") < avant_inf
        invariant_beta(etat)

    def test_l_erreur_est_attribuee_a_la_competence_la_plus_fragile(self) -> None:
        etat = EtatApprenant.initial(profil())
        etat.fixer_maitrise("INF", 0.30, preuves=6)
        etat.fixer_maitrise("VOC", 0.80, preuves=6)
        evenement = integrer_trace(
            etat,
            trace(
                "INF",
                reussite=False,
                competences=("INF", "VOC"),
                identifiant="mixte",
            ),
        )
        assert evenement.responsabilites["INF"] > evenement.responsabilites["VOC"]

    def test_la_reussite_aidee_alimente_surtout_le_canal_assiste(self) -> None:
        etat = EtatApprenant.initial(profil())
        avant_auto = etat.maitrise("INF")
        avant_aide = etat.maitrise_assistee("INF")
        integrer_trace(etat, trace("INF", reussite=True, aides=1, identifiant="aide"))
        assert etat.maitrise_assistee("INF") - avant_aide > etat.maitrise("INF") - avant_auto > 0

    def test_une_reponse_trop_rapide_pese_moins_qu_une_reponse_posee(self) -> None:
        lente = EtatApprenant.initial(profil())
        hative = EtatApprenant.initial(profil())
        for index in range(4):
            integrer_trace(
                lente,
                trace("INF", reussite=False, temps_ms=30000, identifiant=f"l{index}"),
            )
            integrer_trace(
                hative,
                trace("INF", reussite=False, temps_ms=800, identifiant=f"h{index}"),
            )
        assert hative.maitrise("INF") > lente.maitrise("INF")
        assert hative.preuves("INF") < lente.preuves("INF")

    def test_la_relecture_reussie_soutient_la_strategie(self) -> None:
        etat = EtatApprenant.initial(profil())
        avant_str = etat.maitrise("STR")
        avant_reg = etat.maitrise("REG")
        integrer_trace(etat, trace("EXP", reussite=True, relectures=1, identifiant="rel"))
        assert etat.maitrise("STR") > avant_str
        assert etat.maitrise("REG") > avant_reg

    def test_une_confiance_trop_haute_revient_sur_l_autoregulation(self) -> None:
        etat = EtatApprenant.initial(profil())
        avant = etat.maitrise("REG")
        integrer_trace(
            etat,
            trace("EXP", reussite=False, confiance=0.95, identifiant="sur"),
        )
        assert etat.maitrise("REG") < avant

    def test_l_ecoulement_rapproche_du_prior_et_reduit_l_evidence(self) -> None:
        etat = EtatApprenant.initial(profil())
        prior = etat.maitrise("EXP")
        integrer_trace(etat, trace("EXP", reussite=True, moment=0, identifiant="t0"))
        apres = etat.maitrise("EXP")
        preuves = etat.preuves("EXP")
        integrer_trace(
            etat,
            trace("VOC", reussite=True, moment=120, identifiant="t120", seance="s2"),
        )
        assert abs(etat.maitrise("EXP") - prior) < abs(apres - prior)
        assert etat.preuves("EXP") < preuves
        invariant_beta(etat)

    def test_une_trace_anterieure_est_refusee(self) -> None:
        etat = EtatApprenant.initial(profil())
        integrer_trace(etat, trace("EXP", moment=2, identifiant="plus-tard"))
        with pytest.raises(ValueError):
            integrer_trace(etat, trace("EXP", moment=1, identifiant="avant"))

    def test_la_probabilite_croit_avec_la_maitrise_et_avec_l_etayage(self) -> None:
        bas = EtatApprenant.initial(profil())
        haut = bas.copier()
        bas.fixer_maitrise("INF", 0.25, preuves=10)
        haut.fixer_maitrise("INF", 0.80, preuves=10)
        arguments = dict(demande=0.45, difficulte=bas.score_linguistique())
        p_bas = probabilite_reussite(bas, ("INF",), arguments["demande"], arguments["difficulte"], "aucun", "INF")
        p_haut = probabilite_reussite(haut, ("INF",), arguments["demande"], arguments["difficulte"], "aucun", "INF")
        p_aide = probabilite_reussite(
            haut, ("INF",), arguments["demande"], arguments["difficulte"], "connecteurs", "INF"
        )
        p_facile = probabilite_reussite(haut, ("INF",), 0.30, arguments["difficulte"], "aucun", "INF")
        p_dure = probabilite_reussite(haut, ("INF",), 0.80, arguments["difficulte"], "aucun", "INF")
        assert p_haut > p_bas
        assert p_aide > p_haut
        assert p_facile > p_dure


class TestAdaptation:
    def test_sans_observation_le_modele_sonde(self) -> None:
        etat = EtatApprenant.initial(profil())
        decision = decider(etat, IndicateursSeance.vide())
        assert decision.type_decision == "sondage"
        assert decision.etayage == "aucun"
        assert decision.competence_focale == "INF"
        assert "EXP" in decision.competences_concernees
        assert "R9_VALIDATION_ENSEIGNANTE" in decision.regles
        assert decision.validation_enseignante is True
        assert sum(decision.repartition.values()) == pytest.approx(1.0)

    def test_en_cm2_le_sondage_vise_la_justification_sans_oublier_l_explicite(self) -> None:
        decision = decider(EtatApprenant.initial(profil("CM2")), IndicateursSeance.vide())
        assert decision.type_decision == "sondage"
        assert decision.competence_focale == "EVA"
        assert "EXP" in decision.repartition

    def test_retour_au_prerequis_quand_la_cible_est_bloquee(self) -> None:
        etat = EtatApprenant.initial(profil("CP"))
        for code in ORDRE:
            etat.fixer_maitrise(code, min(0.95, attendu("CP", code) + 0.10), preuves=8)
        etat.fixer_maitrise("INF", 0.32, preuves=8)
        etat.fixer_maitrise("COH", 0.44, preuves=8)
        decision = decider(etat, IndicateursSeance.vide())
        assert decision.competence_focale == "COH"
        assert "R5_RETOUR_PREREQUIS" in decision.regles
        assert decision.type_decision == "consolidation"

    def test_les_reponses_hatives_declenchent_la_regulation(self) -> None:
        etat = EtatApprenant.initial(profil())
        modele = ModeleApprenant()
        for index in range(4):
            modele.observer(
                etat,
                trace("INF", reussite=False, temps_ms=700, identifiant=f"h{index}"),
            )
        decision = modele.proposer(etat)
        assert decision.type_decision == "regulation"
        assert decision.nombre_items == 4
        assert decision.etayage != "modelage"
        assert decision.repartition["EXP"] > decision.repartition[decision.competence_focale]

    def test_enrichissement_quand_les_competences_centrales_sont_stables(self) -> None:
        etat = EtatApprenant.initial(profil("CM2"))
        for code in ORDRE:
            etat.fixer_maitrise(code, 0.90, preuves=12)
        decision = decider(etat, IndicateursSeance.vide())
        assert decision.type_decision == "enrichissement"
        assert decision.competence_focale == "MAC"
        assert decision.bande_linguistique == 5
        assert decision.etayage == "aucun"

    def test_le_contrefactuel_enseignant_change_la_cible(self) -> None:
        resultat = simulation_ce2()
        texte = resultat.explication_enseignant.texte
        assert "Inférences" in texte
        assert "0," in texte
        assert "Si « Inférences » était déjà consolidée" in texte
        for mot in MOTS_STIGMATISANTS:
            assert mot not in resultat.explication_enseignant.texte.lower()
            assert mot not in resultat.explication_eleve.texte.lower()
            assert mot not in resultat.explication_famille.texte.lower()

    def test_les_messages_eleve_et_famille_ne_donnent_pas_de_score(self) -> None:
        resultat = simulation_ce2()
        for explication in (resultat.explication_eleve, resultat.explication_famille):
            assert "0," not in explication.texte
            assert "maîtrise autonome" not in explication.texte


class TestScenarioEtGeneration:
    def test_scenario_ce2(self) -> None:
        resultat = simulation_ce2()
        assert resultat.etat.maitrise("EXP") > resultat.etat.maitrise("INF")
        assert resultat.decision.type_decision == "consolidation"
        assert resultat.decision.competence_focale == "INF"
        assert resultat.decision.bande_linguistique == 3
        assert resultat.decision.etayage in {"rappel_strategie", "connecteurs"}
        assert resultat.activite.theme == "animaux"
        assert resultat.activite.alertes_validation == []
        assert "Réponses pour l'enseignant" not in resultat.activite.texte_eleve()
        assert any(question.processus == "INF" for question in resultat.activite.questions)
        invariant_beta(resultat.etat)
        export = resultat.etat.vers_dict()
        assert export["identifiant"] == "eleve-ce2-01"
        assert export["niveau"] == "CE2"
        assert "competences" in export

    def test_theme_hors_liste_revient_a_la_nature(self) -> None:
        modele = ModeleApprenant()
        etat = modele.initialiser(profil(themes=("dinosaures",)))
        specification = modele.specifier(etat)
        assert specification.theme == "nature"
        assert "N'invente aucune maîtrise" in construire_prompt(specification)

    def test_le_validateur_rejette_un_processus_hors_specification(self) -> None:
        modele = ModeleApprenant()
        etat = modele.initialiser(profil())
        specification = modele.specifier(etat)
        activite = Activite(
            titre="Titre",
            theme=specification.theme,
            texte="Un texte court.",
            consigne_eleve="Lis, puis réponds.",
            questions=[
                QuestionActivite("EVA", "Question hors mélange.", "Réponse.", "Indice.")
            ],
            observations=[],
            note_enseignant="",
            alertes_validation=[],
        )
        alertes = valider_activite(activite, specification)
        assert any("EVA" in alerte for alerte in alertes)

    def test_la_seance_suivante_n_emporte_pas_les_indicateurs_precedents(self) -> None:
        modele = ModeleApprenant()
        etat = modele.initialiser(profil())
        for index in range(4):
            modele.observer(
                etat,
                trace("INF", reussite=False, temps_ms=600, identifiant=f"a{index}", seance="s1"),
            )
        assert modele.proposer(etat).type_decision == "regulation"
        modele.observer(
            etat,
            trace("EXP", reussite=True, temps_ms=20000, identifiant="b", seance="s2", moment=1),
        )
        assert modele.indicateurs(etat).nombre == 1
        assert modele.proposer(etat).type_decision != "regulation"

    def test_le_prior_reste_domine_par_une_masse_d_observations(self) -> None:
        etat = EtatApprenant.initial(profil())
        depart = etat.autonome["EXP"].alpha + etat.autonome["EXP"].beta
        assert depart == pytest.approx(KAPPA_PRIOR)
        for index in range(10):
            integrer_trace(etat, trace("EXP", reussite=True, identifiant=f"n{index}"))
        assert etat.preuves("EXP") > KAPPA_PRIOR / 2
        assert etat.maitrise("EXP") > PRIOR["CE2"]["EXP"]
