# sledo

SLEDO (Sequential Learning Engineering Design Optimiser) is a tool for optimising parametric component designs, developed for fusion engineering.

`sledo` uses Bayesian Optimisation to intelligently select candidate designs from a parametric search space and MOOSE to evaluate the design performance via scalable multiphysics simulation.

# Installation

## Linux

We recommend using a python virtual environment to install `sledo`.
Run the following to create and activate a virtual environment in your current working directory.
Skip this step if you intend to install `sledo` into an existing python environment.
```
python3 -m venv venv
source venv/bin/activate
```

### Standard install
From the `sledo` root directory (the directory containing this README), ensure your virtual environment is activated and then run:
```
pip install .
```

If you intend to use the jupyter notebook tutorials and are using a virtual environment, also run the following line (replacing `venv`` with the name of your virtual environment if it is different):
```
# Enable virtual environment in the tutorial notebooks.
python3 -m ipykernel install --user --name=venv
```

`sledo` can now be imported into python as:
```
import sledo
```

To test the installation, run `python3 -c "import sledo"`. If the installation was unsuccessful, an error will be raised.

### Editable install (developer mode)
Developers may wish to create an editable installation. This allows changes to the source code to immediately take effect without the need to re-install `sledo`. This can be useful when running tests and other scripts.

To install `sledo` this way, use the `--editable` flag when running the `pip install` line as follows:
```
# Install as an editable installation.
pip3 install --editable .
```

# Getting started

To start using `sledo`, please refer to the `tutorials` and `examples` folders for example usage.

Before using `sledo`, please see the following section on providing access to your MOOSE application of choice for running simulations.

## MOOSE (Multiphysics Object Oriented Simulation Environment)

While `sledo` itself is a pure python project, it is intended to be used alongside MOOSE.
The simplest way to give `sledo` visibility of your MOOSE installation and chosen MOOSE app is to fill in the required paths in `moose_config.json`.
If you don't have MOOSE installed already, there are several MOOSE applications available alongside `sledo` in the Aurora Multiphysics organisation (https://github.com/aurora-multiphysics), such as `proteus`, `aurora`, and `apollo`; each is focussed on different physics domains, so choose the one appropriate for your design problem.

# Contributors

Luke Humphrey, UK Atomic Energy Authority

Aleksander Dubas, UK Atomic Energy Authority

Andrew Davis, UK Atomic Energy Authority

Lloyd Fletcher, UK Atomic Energy Authority

# Citing Sledo

If using `sledo` in your research, please cite the following:

> Citation TBC

Please also cite `sledo`'s dependencies as indicated on their individual websites:

- MOOSE (https://mooseframework.inl.gov/citing.html)
- Ray-Tune (https://docs.ray.io/en/latest/tune/index.html#citing-tune)
- BoTorch (https://botorch.org/docs/papers)
- NumPy (https://numpy.org/citing-numpy/)
- SciPy (https://scipy.org/citing-scipy/)
- Matplotlib (https://matplotlib.org/stable/users/project/citing.html)
