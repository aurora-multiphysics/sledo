"""
SLEDO MooseHerder/Proteus Monoblock Example

Example input file for running Bayesian optimisation of a simplified divertor
monoblock using MooseHerder as the model instantiation tool and Proteus as the
simulation tool.

(c) Copyright UKAEA 2023-2024.
"""

from pathlib import Path
from ray import tune
from ray.tune.search.ax import AxSearch

from sledo.optimiser import Optimiser
from examples.mooseherder.design_evaluator import DesignEvaluator

MOOSE_OPT = "proteus-opt"
EXAMPLES_DIR = Path(__file__).parent.absolute()
BASE_INPUT_FILE = EXAMPLES_DIR / "input_files" / "monoblock.i"
WORKING_DIR = EXAMPLES_DIR / "results" / "monoblock"

if __name__ == '__main__':

    # Instantiate moose herder class.
    design_evaluator = DesignEvaluator(
        MOOSE_OPT,
        BASE_INPUT_FILE,
        WORKING_DIR,
    )

    # Define design evaluation function.
    def evaluate(parameters):
        data = design_evaluator.evaluate_design(parameters)
        stress = float(data[-1][-1])
        return {"stress": stress}

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
        evaluate,
        search_space,
        "stress",
        AxSearch(),
        20,
        data_dir=WORKING_DIR,
    )

    results = opt.run_optimisation()

    # Save the optimiser class instance to file.
    opt.pickle()
