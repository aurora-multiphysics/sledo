"""
SLEDO Simple Monoblock Example

Example input file for running Bayesian optimisation of a simplified divertor
monoblock to minimise the peak von misses stress predicted by a
thermomechanical MOOSE simulation.

(c) Copyright UKAEA 2023-2024.
"""

from ray import tune

from sledo import Optimiser, MooseHerderDesignEvaluator
from sledo import SLEDO_ROOT, MOOSE_CONFIG_FILE

EXAMPLES_DIR = SLEDO_ROOT / "examples"
INPUT_FILE = EXAMPLES_DIR / "input_files" / "simple_monoblock_thermomech.i"
WORKING_DIR = EXAMPLES_DIR / "results" / "example_1"
METRICS = ["max_stress"]

if __name__ == "__main__":

    # Instantiate design evaluator.
    design_evaluator = MooseHerderDesignEvaluator(
        METRICS,
        INPUT_FILE,
        working_dir=WORKING_DIR,
        config_path=MOOSE_CONFIG_FILE,
    )

    # Define a search space according to the Ray Tune API.
    # Documentation here:
    # https://docs.ray.io/en/latest/tune/api/search_space.html
    search_space = {
        "monoBArmHeight": tune.uniform(1e-3, 20e-3),
        "monoBThick": tune.uniform(0.5e-3, 9e-3),
    }

    # Instantiate SLEDO optimiser.
    opt = Optimiser(
        "simple-monoblock-optimiser",
        design_evaluator,
        search_space,
        20,
        data_dir=WORKING_DIR,
    )

    results = opt.run_optimisation()
    print(results)

    # Save the optimiser class instance to file.
    opt.pickle()
