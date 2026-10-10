"""Lance le scénario illustratif de CE2."""

from modele_apprenant.demonstration import formater_rapport, simulation_ce2


def main() -> None:
    print(formater_rapport(simulation_ce2()))


if __name__ == "__main__":
    main()
