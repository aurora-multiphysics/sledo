"""
Monoblock thermal model catbird implementation.

(c) Copyright UKAEA 2023-2024.
"""

from catbird import (
    Factory,
    MooseModel,
)
import math


# This is how we enable syntax
# Only enable what you need, or it runs slowly!
class MonoblockFactory(Factory):
    def set_defaults(self):
        executioner_enable_dict = {"obj_type": ["Steady", "Transient"]}
        self.enable_syntax("Executioner", executioner_enable_dict)
        self.enable_syntax("Mesh")
        self.enable_syntax("Variables")
        self.enable_syntax("Kernels")
        self.enable_syntax("Functions")
        self.enable_syntax("Materials")
        self.enable_syntax("BCs")
        self.enable_syntax("Preconditioning")
        self.enable_syntax("Postprocessors")
        self.enable_syntax("Outputs")


# Just a struct to store geometric parameters
class MonoblockGeometry:
    def __init__(self):
        self.pipeThick = 1.5e-3  # m
        self.pipeIntDiam = 12e-3  # m
        self.intLayerThick = 1e-3  # m
        self.monoBThick = 3e-3  # m
        self.monoBArmHeight = 8e-3  # m
        self.monoBDepth = 12e-3  # m
        self.pipeExtDiam = self.pipeIntDiam + 2 * self.pipeThick
        self.intLayerIntDiam = self.pipeExtDiam
        self.intLayerExtDiam = self.intLayerIntDiam + 2 * self.intLayerThick
        self.monoBWidth = self.intLayerExtDiam + 2 * self.monoBThick
        self.pipeIntCirc = math.pi * self.pipeIntDiam

        # Mesh Sizing
        self.meshRefFact = 1
        self.meshDens = 1e3  # divisions per metre (nominal)

        # Number of divisions along the top section of the monoblock armour.
        self.monoBArmDivs = int(
            self.monoBArmHeight * self.meshDens * self.meshRefFact
        )

        # Number of divisions around each quadrant of the circumference of the
        # pipe, interlayer, and radial section of the monoblock armour.
        self.pipeCircSectDivs = 2 * int(
            self.monoBWidth / 2 * self.meshDens * self.meshRefFact / 2
        )

        # Number of radial divisions for the pipe, interlayer, and radial
        # section of the monoblock armour respectively.
        self.pipeRadDivs = max(
            int(self.pipeThick * self.meshDens * self.meshRefFact), 3
        )
        self.intLayerRadDivs = max(
            int(self.intLayerThick * self.meshDens * self.meshRefFact), 5
        )
        self.monoBRadDivs = max(
            int(
                (self.monoBWidth - self.intLayerExtDiam)
                / 2
                * self.meshDens
                * self.meshRefFact
            ),
            5,
        )

        # Number of divisions along monoblock depth (i.e. z-dimension).
        self.extrudeDivs = max(
            2 * int(self.monoBDepth * self.meshDens * self.meshRefFact / 2), 4
        )
        self.monoBElemSize = self.monoBDepth / self.extrudeDivs
        self.tol = self.monoBElemSize / 10
        self.ctol = self.pipeIntCirc / (8 * 4 * self.pipeCircSectDivs)


# This class represents the boilerplate input deck
class MonoblockModel(MooseModel):
    def load_default_syntax(self):
        self.add_syntax("Mesh", action="SetupMeshAction")
        self.add_syntax("Variables")
        self.add_syntax("Kernels")
        # self.add_syntax("Functions")
        self.add_syntax("Materials")
        self.add_syntax("BCs")
        self.add_syntax("Preconditioning")
        self.add_syntax("Executioner", obj_type="Steady")
        self.add_syntax("Postprocessors")
        self.add_syntax("Outputs", action="CommonOutputAction")

    def __init__(self, factory_in):
        super().__init__(factory_in)
        assert isinstance(factory_in, MonoblockFactory)
        self._geom = MonoblockGeometry()
        self._concretise_model()

    def modify_parameters(self, new_parameters: dict):
        for param in new_parameters:
            value = new_parameters[param]
            setattr(self._geom, param, value)

    def _concretise_model(self):
        # Set executioner attributes
        self.executioner.solve_type = "PJFNK"
        self.executioner.petsc_options_iname = "-pc_type -pc_hypre_type"
        self.executioner.petsc_options_value = "hypre boomeramg"

        # Add a preconditioner
        self.add_preconditioner("smp", "SMP", full=True)

        # Set mesh attributes
        self.second_order = False

        # Add mesh generators (using kwarg syntax)
        self.add_mesh_generator(
            "mesh_monoblock",
            "PolygonConcentricCircleMeshGenerator",
            num_sides=4,
            polygon_size=self._geom.monoBWidth / 2,
            polygon_size_style="apothem",
            ring_radii=[
                self._geom.pipeIntDiam / 2,
                self._geom.pipeExtDiam / 2,
                self._geom.intLayerExtDiam / 2,
            ],
            num_sectors_per_side=[
                self._geom.pipeCircSectDivs,
                self._geom.pipeCircSectDivs,
                self._geom.pipeCircSectDivs,
                self._geom.pipeCircSectDivs,
            ],
            ring_intervals=[
                1,
                self._geom.pipeRadDivs,
                self._geom.intLayerRadDivs,
            ],
            background_intervals=self._geom.monoBRadDivs,
            preserve_volumes="on",
            flat_side_up=True,
            ring_block_names="void pipe interlayer",
            background_block_names="monoblock",
            interface_boundary_id_shift=1000,
            external_boundary_name="monoblock_boundary",
            generate_side_specific_boundaries=True,
        )

        self.add_mesh_generator(
            "mesh_armour",
            "GeneratedMeshGenerator",
            dim=2,
            xmin=(self._geom.monoBWidth / -2),
            xmax=(self._geom.monoBWidth / 2),
            ymin=(self._geom.monoBWidth / 2),
            ymax=(self._geom.monoBWidth / 2 + self._geom.monoBArmHeight),
            nx=(self._geom.pipeCircSectDivs),
            ny=(self._geom.monoBArmDivs),
            boundary_name_prefix="armour",
        )

        self.add_mesh_generator(
            "combine_meshes",
            "StitchedMeshGenerator",
            inputs="mesh_monoblock mesh_armour",
            stitch_boundaries_pairs="monoblock_boundary armour_bottom",
            clear_stitched_boundary_ids=True,
        )

        self.add_mesh_generator(
            "delete_void",
            "BlockDeletionGenerator",
            input="combine_meshes",
            block="void",
            new_boundary="internal_boundary",
        )

        self.add_mesh_generator(
            "merge_block_names",
            "RenameBlockGenerator",
            input="delete_void",
            old_block="4 0",
            new_block="armour armour",
        )

        self.add_mesh_generator(
            "merge_boundary_names",
            "RenameBoundaryGenerator",
            input="merge_block_names",
            old_boundary=(
                "armour_top armour_left 10002 15002 armour_right 10004 "
                "15004 10003 15003"
            ),
            new_boundary="top left left left right right right bottom bottom",
        )

        self.add_mesh_generator(
            "extrude",
            "AdvancedExtruderGenerator",
            input="merge_boundary_names",
            direction="0 0 1",
            heights=self._geom.monoBDepth,
            num_layers=self._geom.extrudeDivs,
        )

        self.add_mesh_generator(
            "name_node_centre_x_bottom_y_back_z",
            "BoundingBoxNodeSetGenerator",
            input="extrude",
            bottom_left=[
                -self._geom.ctol,
                (self._geom.monoBWidth / -2) - self._geom.ctol,
                -self._geom.tol,
            ],
            top_right=[
                self._geom.ctol,
                (self._geom.monoBWidth / -2) + self._geom.ctol,
                self._geom.tol,
            ],
            new_boundary="centre_x_bottom_y_back_z",
        )

        self.add_mesh_generator(
            "name_node_centre_x_bottom_y_front_z",
            "BoundingBoxNodeSetGenerator",
            input="name_node_centre_x_bottom_y_back_z",
            bottom_left=[
                -self._geom.ctol,
                (self._geom.monoBWidth / -2) - self._geom.ctol,
                self._geom.monoBDepth - self._geom.tol,
            ],
            top_right=[
                self._geom.ctol,
                (self._geom.monoBWidth / -2) + self._geom.ctol,
                self._geom.monoBDepth + self._geom.tol,
            ],
            new_boundary="centre_x_bottom_y_front_z",
        )

        self.add_mesh_generator(
            "name_node_left_x_bottom_y_centre_z",
            "BoundingBoxNodeSetGenerator",
            input="name_node_centre_x_bottom_y_front_z",
            bottom_left=[
                (self._geom.monoBWidth / -2) - self._geom.ctol,
                (self._geom.monoBWidth / -2) - self._geom.ctol,
                (self._geom.monoBDepth / 2) - self._geom.tol,
            ],
            top_right=[
                (self._geom.monoBWidth / -2) + self._geom.ctol,
                (self._geom.monoBWidth / -2) + self._geom.ctol,
                (self._geom.monoBDepth / 2) + self._geom.tol,
            ],
            new_boundary="left_x_bottom_y_centre_z",
        )

        self.add_mesh_generator(
            "name_node_right_x_bottom_y_centre_z",
            "BoundingBoxNodeSetGenerator",
            input="name_node_left_x_bottom_y_centre_z",
            bottom_left=[
                (self._geom.monoBWidth / 2) - self._geom.ctol,
                (self._geom.monoBWidth / -2) - self._geom.ctol,
                (self._geom.monoBDepth / 2) - self._geom.tol,
            ],
            top_right=[
                (self._geom.monoBWidth / 2) + self._geom.ctol,
                (self._geom.monoBWidth / -2) + self._geom.ctol,
                (self._geom.monoBDepth / 2) + self._geom.tol,
            ],
            new_boundary="right_x_bottom_y_centre_z",
        )

        # Add variables
        var_name = "temperature"
        coolantTemp = 150  # degC
        self.add_variable(
            var_name,
            family="LAGRANGE",
            order="FIRST",
            initial_condition=coolantTemp,
        )

        # Add kernels
        self.add_kernel(
            "heat_conduction", kernel_type="HeatConduction", variable=var_name
        )

        # Not needed for thermal problem
        # # Add functions
        # self.add_function("cucrzr_thermal_expansion",function_type="PiecewiseLinear",
        #                    xy_data=[ 20, 1.67e-05,
        #                              50, 1.7e-05,
        #                              100, 1.73e-05,
        #                              150, 1.75e-05,
        #                              200, 1.77e-05,
        #                              250, 1.78e-05,
        #                              300, 1.8e-05,
        #                              350, 1.8e-05,
        #                              400, 1.81e-05,
        #                              450, 1.82e-05,
        #                              500, 1.84e-05,
        #                              550, 1.85e-05,
        #                              600, 1.86e-05 ] )

        # self.add_function("copper_thermal_expansion",function_type="PiecewiseLinear",
        #                    xy_data=[20, 1.67e-05,
        #                             50, 1.7e-05,
        #                             100, 1.72e-05,
        #                             150, 1.75e-05,
        #                             200, 1.77e-05,
        #                             250, 1.78e-05,
        #                             300, 1.8e-05,
        #                             350, 1.81e-05,
        #                             400, 1.82e-05,
        #                             450, 1.84e-05,
        #                             500, 1.85e-05,
        #                             550, 1.87e-05,
        #                             600, 1.88e-05,
        #                             650, 1.9e-05,
        #                             700, 1.91e-05,
        #                             750, 1.93e-05,
        #                             800, 1.96e-05,
        #                             850, 1.98e-05,
        #                             900, 2.01e-05])

        # self.add_function("tungsten_thermal_expansion",function_type="PiecewiseLinear",
        #                    xy_data=[20,   4.5e-06,
        #                             100,  4.5e-06,
        #                             200,  4.53e-06,
        #                             300,  4.58e-06,
        #                             400,  4.63e-06,
        #                             500,  4.68e-06,
        #                             600,  4.72e-06,
        #                             700,  4.76e-06,
        #                             800,  4.81e-06,
        #                             900,  4.85e-06,
        #                             1000, 4.89e-06,
        #                             1200, 4.98e-06,
        #                             1400, 5.08e-06,
        #                             1600, 5.18e-06,
        #                             1800, 5.3e-06,
        #                             2000, 5.43e-06,
        #                             2200, 5.57e-06,
        #                             2400, 5.74e-06,
        #                             2600, 5.93e-06,
        #                             2800, 6.15e-06,
        #                             3000, 6.4e-06,
        #                             3200, 6.67e-06])

        # Add materials
        # Thermal conductivities
        self.add_material(
            "cucrzr_thermal_conductivity",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                318,
                50,
                324,
                100,
                333,
                150,
                339,
                200,
                343,
                250,
                345,
                300,
                346,
                350,
                347,
                400,
                347,
                450,
                346,
                500,
                346,
            ],
            variable=var_name,
            property="thermal_conductivity",
            block="pipe",
        )

        self.add_material(
            "copper_thermal_conductivity",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                401,
                50,
                398,
                100,
                395,
                150,
                391,
                200,
                388,
                250,
                384,
                300,
                381,
                350,
                378,
                400,
                374,
                450,
                371,
                500,
                367,
                550,
                364,
                600,
                360,
                650,
                357,
                700,
                354,
                750,
                350,
                800,
                347,
                850,
                344,
                900,
                340,
                950,
                337,
                1000,
                334,
            ],
            variable=var_name,
            property="thermal_conductivity",
            block="interlayer",
        )

        self.add_material(
            "tungsten_thermal_conductivity",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                173,
                50,
                170,
                100,
                165,
                150,
                160,
                200,
                156,
                250,
                151,
                300,
                147,
                350,
                143,
                400,
                140,
                450,
                136,
                500,
                133,
                550,
                130,
                600,
                127,
                650,
                125,
                700,
                122,
                750,
                120,
                800,
                118,
                850,
                116,
                900,
                114,
                950,
                112,
                1000,
                110,
                1100,
                108,
                1200,
                105,
            ],
            variable=var_name,
            property="thermal_conductivity",
            block="armour",
        )

        # Densities
        self.add_material(
            "cucrzr_density",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                8900,
                50,
                8886,
                100,
                8863,
                150,
                8840,
                200,
                8816,
                250,
                8791,
                300,
                8797,
                350,
                8742,
                400,
                8716,
                450,
                8691,
                500,
                8665,
            ],
            variable=var_name,
            property="density",
            block="pipe",
        )

        self.add_material(
            "copper_density",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                8940,
                50,
                8926,
                100,
                8903,
                150,
                8879,
                200,
                8854,
                250,
                8829,
                300,
                8802,
                350,
                8774,
                400,
                8744,
                450,
                8713,
                500,
                8681,
                550,
                8647,
                600,
                8612,
                650,
                8575,
                700,
                8536,
                750,
                8495,
                800,
                8453,
                850,
                8409,
                900,
                8363,
            ],
            variable=var_name,
            property="density",
            block="interlayer",
        )

        self.add_material(
            "tungsten_density",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                19300,
                50,
                19290,
                100,
                19280,
                150,
                19270,
                200,
                19250,
                250,
                19240,
                300,
                19230,
                350,
                19220,
                400,
                19200,
                450,
                19190,
                500,
                19180,
                550,
                19170,
                600,
                19150,
                650,
                19140,
                700,
                19130,
                750,
                19110,
                800,
                19100,
                850,
                19080,
                900,
                19070,
                950,
                19060,
                1000,
                19040,
                1100,
                19010,
                1200,
                18990,
            ],
            variable=var_name,
            property="density",
            block="armour",
        )

        # Specific heats
        self.add_material(
            "cucrzr_specific_heat",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                390,
                50,
                393,
                100,
                398,
                150,
                402,
                200,
                407,
                250,
                412,
                300,
                417,
                350,
                422,
                400,
                427,
                450,
                432,
                500,
                437,
                550,
                442,
                600,
                447,
                650,
                452,
                700,
                458,
            ],
            variable=var_name,
            property="specific_heat",
            block="pipe",
        )

        self.add_material(
            "copper_specific_heat",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                388,
                50,
                390,
                100,
                394,
                150,
                398,
                200,
                401,
                250,
                406,
                300,
                410,
                350,
                415,
                400,
                419,
                450,
                424,
                500,
                430,
                550,
                435,
                600,
                441,
                650,
                447,
                700,
                453,
                750,
                459,
                800,
                466,
                850,
                472,
                900,
                479,
                950,
                487,
                1000,
                494,
            ],
            variable=var_name,
            property="specific_heat",
            block="interlayer",
        )

        self.add_material(
            "tungsten_specific_heat",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                20,
                129,
                50,
                130,
                100,
                132,
                150,
                133,
                200,
                135,
                250,
                136,
                300,
                138,
                350,
                139,
                400,
                141,
                450,
                142,
                500,
                144,
                550,
                145,
                600,
                147,
                650,
                148,
                700,
                150,
                750,
                151,
                800,
                152,
                850,
                154,
                900,
                155,
                950,
                156,
                1000,
                158,
                1100,
                160,
                1200,
                163,
            ],
            variable=var_name,
            property="specific_heat",
            block="armour",
        )

        self.add_material(
            "coolant_heat_transfer_coefficient",
            "PiecewiseLinearInterpolationMaterial",
            xy_data=[
                1,
                4,
                100,
                109.1e3,
                150,
                115.9e3,
                200,
                121.01e3,
                250,
                128.8e3,
                295,
                208.2e3,
            ],
            variable=var_name,
            property="heat_transfer_coefficient",
            boundary="internal_boundary",
        )

        # Add boundary conditions
        surfHeatFlux = 10e6  # W/m^2
        self.add_bc(
            "heat_flux_in",
            "NeumannBC",
            variable=var_name,
            boundary="top",
            value=surfHeatFlux,
        )

        self.add_bc(
            "heat_flux_out",
            "ConvectiveHeatFluxBC",
            variable=var_name,
            boundary="internal_boundary",
            T_infinity=coolantTemp,
            heat_transfer_coefficient="heat_transfer_coefficient",
        )

        # Add Exodus output
        self.outputs.exodus = True

        # Add postprocessor
        self.add_postprocessor(
            "max_temp", "ElementExtremeValue", variable=var_name
        )
