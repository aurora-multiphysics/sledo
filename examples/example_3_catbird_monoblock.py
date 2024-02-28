"""
SLEDO Monoblock Example

Example input file for running Bayesian optimisation of a divertor monoblock
to minimise the peak temperature predicted by a thermal MOOSE simulation.

In this example, catbird is used to generate input files without the need for
a user-supplied input file to use as a base.

(c) Copyright UKAEA 2023-2024.
"""

from ray import tune

from sledo import Optimiser, CatBirdMooseHerderDesignEvaluator
from sledo import SLEDO_ROOT, MOOSE_CONFIG_FILE

EXAMPLES_DIR = SLEDO_ROOT / "examples"
WORKING_DIR = EXAMPLES_DIR / "results" / "example_3"

METRICS = ["temperature"]

if __name__ == "__main__":

    # Instantiate design evaluator.
    design_evaluator = CatBirdMooseHerderDesignEvaluator(
        METRICS,
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
