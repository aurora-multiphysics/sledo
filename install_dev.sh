#!/usr/bin/env bash
#
# SLEDO installation script.
#
# (c) Copyright UKAEA 2023.

# Install sledo as an editable installation.
echo "Installing sledo in developer mode..."
pip3 install --editable .

# Allow jupyter notebooks to use the virtual environment.
python3 -m ipykernel install --user --name=venv

# Notify user.
echo "Install complete."
echo ""
echo "Please ensure you add pyhit and moosetree to your python path by adding the following lines to your bashrc file:"
echo "export PYTHONPATH=\${PYTHONPATH}:/path/to/moose/python/pyhit"
echo "export PYTHONPATH=\${PYTHONPATH}:/path/to/moose/python/moosetree"
