"""
SLEDO Monoblock Example

Example input file for running Bayesian optimisation of a divertor monoblock
to minimise the peak von misses stress predicted by a thermomechanical
MOOSE simulation.

(c) Copyright UKAEA 2023-2024.
"""

from ray import tune

from sledo import Optimiser, MooseHerderDesignEvaluator
from sledo import SLEDO_ROOT, MOOSE_CONFIG_FILE

EXAMPLES_DIR = SLEDO_ROOT / "examples" / "mooseherder"
INPUT_FILE = EXAMPLES_DIR / "input_files" / "monoblock_thermomech.i"
WORKING_DIR = EXAMPLES_DIR / "results" / "simple_monoblock_thermomech"
METRICS = ["max_stress"]

if __name__ == "__main__":

    # Instantiate design evaluator.
    design_evaluator = MooseHerderDesignEvaluator(
        METRICS,
        INPUT_FILE,
        working_dir=WORKING_DIR,
        config_path=MOOSE_CONFIG_FILE,
    )

    # Define a search space according to the ray tune API.
    # Documentation here:
    # https://docs.ray.io/en/latest/tune/api/search_space.html
    search_space = {
        "pipeThick": tune.uniform(1e-3, 6e-3),
        "intLayerThick": tune.uniform(1e-3, 6e-3),
        "monoBThick": tune.uniform(1e-3, 6e-3),
        "monoBArmHeight": tune.uniform(1e-3, 16e-3),
    }

    # Instantiate SLEDO optimiser.
    opt = Optimiser(
        "monoblock-optimiser",
        design_evaluator,
        search_space,
        20,
        data_dir=WORKING_DIR,
    )

    results = opt.run_optimisation()
    print(results)

    # Save the optimiser class instance to file.
    opt.pickle()
