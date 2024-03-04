"""
SLEDO Paths

(c) Copyright UKAEA 2023-2024.
"""

from pathlib import Path

SLEDO_ROOT = Path(__file__).parent.parent.parent.absolute()
MOOSE_CONFIG_FILE = SLEDO_ROOT / "moose_config.json"
