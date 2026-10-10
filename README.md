# Modèle de l'apprenant en compréhension écrite

Modèle intelligent, dynamique et explicable pour l'adaptation pédagogique en compréhension écrite à l'école élémentaire. Il relie un diagnostic symbolique, des indicateurs de learning analytics et une génération d'activités contrainte.

La conception complète est dans [`docs/conception-modele-apprenant.md`](docs/conception-modele-apprenant.md).

Le diagnostic de maîtrise est calculé par le modèle symbolique. Le générateur rédige une activité à partir d'une spécification déjà décidée. L'enseignant valide la proposition avant de la présenter à l'élève. Les priors et les poids sont des hypothèses provisoires, à calibrer sur des données de classe.

## Lancer

```bash
pip install -e ".[dev]"
python3 -m pytest
python3 exemples/scenario_ce2.py
```

Le scénario suit un élève de CE2, pseudonymisé, qui réussit le prélèvement explicite et consolide encore les inférences. Il affiche la décision, les explications enseignant, élève et famille, puis une activité sur le thème choisi.

## Organisation

| Emplacement | Rôle |
| --- | --- |
| `src/modele_apprenant/ontologie.py` | Compétences, prérequis, priors, attendus |
| `src/modele_apprenant/etat.py` | Canaux autonome et assisté, écoulement du temps |
| `src/modele_apprenant/inference.py` | Mise à jour explicable |
| `src/modele_apprenant/analytique.py` | Indicateurs de séance |
| `src/modele_apprenant/adaptation.py` | Politique d'adaptation |
| `src/modele_apprenant/explication.py` | Explications selon le public |
| `src/modele_apprenant/generation.py` | Spécification, gabarits, validation |
| `src/modele_apprenant/constantes.py` | Hyperparamètres provisoires |
