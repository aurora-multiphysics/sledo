"""
SLEDO MooseHerder/Proteus Simple Monoblock Example

Example input file for running Bayesian optimisation of a simplified divertor
monoblock using MooseHerder as the model instantiation tool and Proteus as the
simulation tool.

(c) Copyright UKAEA 2023-2024.
"""

from pathlib import Path
from ray import train, tune
from ray.tune.search.ax import AxSearch

from examples.mooseherder.mooseherder import MooseHerder

MOOSE_OPT = "proteus-opt"
EXAMPLES_DIR = Path(__file__).parent.absolute()
BASE_INPUT_FILE = EXAMPLES_DIR / "input_files" / "simple_monoblock.i"
WORKING_DIR = EXAMPLES_DIR / "results" / "simple_monoblock"

if __name__ == '__main__':

    # Instantiate moose herder class.
    proteus_herder = MooseHerder(
        MOOSE_OPT,
        BASE_INPUT_FILE,
        WORKING_DIR,
    )

    # Define design evaluation function.
    def evaluate(parameters):
        data = proteus_herder.evaluate_design(parameters)
        stress = float(data[-1][-1])
        train.report({"stress": stress})

    # Define a search space according to the Ray Tune API.
    # Documentation here:
    # https://docs.ray.io/en/latest/tune/api/search_space.html
    search_space = {
        "monoBArmHeight": tune.uniform(1e-3, 20e-3),
        "monoBThick": tune.uniform(0.5e-3, 9e-3),
    }

    # Define the search algorithm.
    search_alg = AxSearch()

    # Set the maximum number of concurrent trials.
    search_alg = tune.search.ConcurrencyLimiter(search_alg, max_concurrent=1)

    # Set the number of component designs to trial.
    num_samples = 20

    tuner = tune.Tuner(
        evaluate,
        tune_config=tune.TuneConfig(
            metric="stress",
            mode="min",
            search_alg=search_alg,
            num_samples=num_samples,
        ),
        run_config=train.RunConfig(
            name="ax",
        ),
        param_space=search_space,
    )
    results = tuner.fit()
