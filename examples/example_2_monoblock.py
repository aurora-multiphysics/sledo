from sledo.optimiser import Optimiser
from sledo.simulation import ThermoMechSimulation

DATA_DIR = "./results/example_2"

search_space = (
    {
        "name": "Pipe thickness",
        "type": "range",
        "hit_name": "pipeThick",
        "hit_block": "",
        "bounds": [1e-3, 6e-3],
    },
    {
        "name": "Interlayer thickness",
        "type": "range",
        "hit_name": "intLayerThick",
        "hit_block": "",
        "bounds": [1e-3, 6e-3],
    },
    {
        "name": "Block thickness",
        "type": "range",
        "hit_name": "monoBThick",
        "hit_block": "",
        "bounds": [1e-3, 6e-3],
    },
    {
        "name": "Armour height",
        "type": "range",
        "hit_name": "monoBArmHeight",
        "hit_block": "",
        "bounds": [1e-3, 16e-3],
    },
)

opt = Optimiser(
    name="monoblock",
    search_space=search_space,
    simulation_class=ThermoMechSimulation,
    data_dir=DATA_DIR,
)

opt.load_input_file("./input_files/monoblock.i")
opt.run_optimisation_loop(
    objective_name="stress",
    max_iter=20,
    minimise=True,
)

opt.pickle()
