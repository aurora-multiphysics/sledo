from sledo.optimiser import (
    Optimiser,
)

import pytest
import pathlib

import pyhit
import moosetree

from sledo.simulation import ThermoMechSimulation

TEST_DATA_DIR = pathlib.Path("./tests/test_data/")
TEST_SEARCH_SPACE = (
    {
        "name": "Length",
        "type": "range",
        "bounds": [1, 10],
        "hit_block": "/Mesh/gen",
        "hit_name": "xmax",
    },
    {
        "name": "U",
        "type": "range",
        "bounds": [100, 200],
        "hit_block": "/BCs/left",
        "hit_name": "value",
    },
    {
        "name": "Pi",
        "type": "range",
        "bounds": [3.13, 3.15],
        "hit_block": "",
        "hit_name": "PI",
    },
)


@pytest.fixture(scope="session")
def tmp_data_dir(tmp_path_factory):
    tmp_data_dir = tmp_path_factory.mktemp("tmp_data_dir")
    return tmp_data_dir


class TestOptimiser:
    """
    Tests for the SLEDO Optimiser class.
    """

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_data_dir):
        self.opt = Optimiser(
            name="simple_monoblock",
            simulation_class=ThermoMechSimulation,
            search_space=TEST_SEARCH_SPACE,
            data_dir=tmp_data_dir,
        )

    def test_init(self):
        """Test Optimiser class initiates correctly."""
        assert self.opt.data_dir.is_dir()

    def test_load_input_file(self):
        """
        Test Optimiser can load a MOOSE input file correctly and save a
        copy in the data dir.
        """
        # Test the file to be loaded exists.
        path_to_file = TEST_DATA_DIR / "input.i"
        assert path_to_file.is_file()

        # Test a copy does not already exist.
        path_to_copy = self.opt.data_dir / "input_unmodified.i"
        assert not path_to_copy.is_file()

        # Load input file and test that both the original and the copy exist.
        self.opt.load_input_file(path_to_file)
        assert path_to_file.is_file()
        assert path_to_copy.is_file()

    def test_generate_modified_file(self):
        """Test Optimiser can generate a modified input file correctly."""
        # Load the input file.
        path_to_file = TEST_DATA_DIR / "input.i"
        self.opt.load_input_file(path_to_file)

        # Generate modified input file and test that the new file exists.
        filename = "input_modified"
        filename_with_ext = filename + ".i"
        new_params = {
            "Length": 4,
            "U": 200,
        }
        path_to_modified_file = self.opt.data_dir / filename_with_ext
        assert not path_to_modified_file.is_file()
        self.opt.generate_modified_file(filename, new_params=new_params)
        assert path_to_modified_file.is_file()

        # Test that the new file has the expected lines modified.
        root = pyhit.load(str(path_to_modified_file))
        mesh = moosetree.find(root, func=lambda n: n.fullpath == "/Mesh/gen")
        leftbc = moosetree.find(root, func=lambda n: n.fullpath == "/BCs/left")
        assert mesh.get("xmax") == new_params["Length"]
        assert leftbc.get("value") == new_params["U"]

        # Test that the original file and copy are left unmodified.
        path_to_copy = self.opt.data_dir / "input_unmodified.i"
        for path in (path_to_file, path_to_copy):
            root = pyhit.load(str(path))
            mesh = moosetree.find(
                root, func=lambda n: n.fullpath == "/Mesh/gen"
            )
            left_bc = moosetree.find(
                root, func=lambda n: n.fullpath == "/BCs/left"
            )
            assert mesh.get("xmax") == 3
            assert left_bc.get("value") == 300

    def test_generate_modified_file_root(self):
        """
        Test Optimiser can generate a modified input file correctly in the
        case that the parameters to modify are in the moosetree root.
        """
        # Load the input file.
        path_to_file = TEST_DATA_DIR / "input.i"
        self.opt.load_input_file(path_to_file)

        # Generate modified input file and test that the new file exists.
        filename = "input_modified"
        filename_with_ext = filename + ".i"
        new_params = {
            "Pi": 6.28,
        }
        path_to_modified_file = self.opt.data_dir / filename_with_ext
        assert not path_to_modified_file.is_file()
        self.opt.generate_modified_file(filename, new_params=new_params)
        assert path_to_modified_file.is_file()

        # Test that the new file has the expected lines modified.
        root = pyhit.load(str(path_to_modified_file))
        assert root.get("PI") == new_params["Pi"]

        # Test that the original file and copy are left unmodified.
        path_to_copy = self.opt.data_dir / "input_unmodified.i"
        for path in (path_to_file, path_to_copy):
            root = pyhit.load(str(path))
            assert root.get("PI") == 3.14
