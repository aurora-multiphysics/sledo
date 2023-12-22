"""
SLEDO Simple Monoblock Example

Example input file for running Bayesian optimisation of a simplified divertor
monoblock.

(c) Copyright UKAEA 2023.
"""

from sledo.optimiser import Optimiser
from sledo.simulation import ThermoMechSimulation
from ray import tune

DATA_DIR = "./results/example_simple_monoblock"

if __name__ == '__main__':

    # Define a search space according to the Ray Tune API.
    # Documentation here:
    # https://docs.ray.io/en/latest/tune/api/search_space.html
    search_space = {
        "Armour height": tune.uniform(1e-3, 20e-3),
        "Block width": tune.uniform(17e-3, 34e-3),
    }

    # Instantiate the Sledo Optimiser class.
    opt = Optimiser(
        name="simple_monoblock",
        search_space=search_space,
        simulation_class=ThermoMechSimulation,
        data_dir=DATA_DIR,
    )

    opt.run_optimisation_loop(
        objective_name="stress",
        max_iter=20,
        minimise=True,
    )

    opt.pickle()
