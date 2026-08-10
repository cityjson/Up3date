"""Blender-dependent implementation of the Up3date add-on."""

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .core import operator, prop, ui
from .core.blender_types import BlenderContext, Menu
from .core.objects import CityJSONExporter, CityJSONParser


class ImportCityJSON(Operator, ImportHelper):
    "Load a CityJSON file"

    bl_idname = "cityjson.import_file"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import CityJSON"

    # ImportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    material_type: EnumProperty(
        name="Materials' type",
        items=(
            (
                "SURFACES",
                "Surfaces",
                "Creates materials based on semantic surface types",
            ),
            (
                "CITY_OBJECTS",
                "City Objects",
                "Creates materials based on the type of city object",
            ),
        ),
        description=("Create materials based on city object or semantic surfaces"),
    )

    reuse_materials: BoolProperty(
        name="Reuse materials",
        description="Use common materials according to surface type",
        default=True,
    )

    clean_scene: BoolProperty(
        name="Clean scene",
        description="Remove existing objects from the scene before importing",
        default=True,
    )

    def execute(self, context: BlenderContext) -> set[str]:
        """Executes the import process"""

        parser = CityJSONParser(
            self.filepath,
            material_type=self.material_type,
            reuse_materials=self.reuse_materials,
            clear_scene=self.clean_scene,
        )

        return parser.execute()


class ExportCityJSON(Operator, ExportHelper):
    "Export scene as a CityJSON file"

    bl_idname = "cityjson.export_file"
    bl_label = "Export CityJSON"

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={"HIDDEN"},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    check_for_duplicates: BoolProperty(
        name="Remove vertex duplicates",
        default=True,
    )

    precision: IntProperty(
        name="Precision",
        default=5,
        description="Decimals to check for vertex duplicates",
        min=0,
        max=12,
    )
    # single_lod_switch: BoolProperty(
    #     name="Export single LoD",
    #     description="Enable to export only a single LoD",
    #     default=False,
    #     )

    # export_single_lod: EnumProperty(
    #     name="Select LoD :",
    #     items=(('LoD0', "LoD 0",
    #             "Export only LoD 0"),
    #         ('LoD1', "LoD 1",
    #             "Export only LoD 1"),
    #         ('LoD2', "LoD 2",
    #             "Export only LoD 2"),
    #             ),
    #     description=(
    #         "Select which LoD should be exported"
    #     )
    # )
    def execute(self, context: BlenderContext) -> set[str]:

        exporter = CityJSONExporter(
            self.filepath,
            check_for_duplicates=self.check_for_duplicates,
            precision=self.precision,
        )
        return exporter.execute()


classes = (
    ImportCityJSON,
    ExportCityJSON,
    prop.Up3dateCityJSONfyProperties,
    operator.Up3dateCityJsonfy,
    ui.Up3datePTgui,
)


def menu_func_export(self: Menu, context: BlenderContext) -> None:
    """Defines the menu item for CityJSON import"""
    self.layout.operator(ExportCityJSON.bl_idname, text="CityJSON (.json)")


def menu_func_import(self: Menu, context: BlenderContext) -> None:
    """Defines the menu item for CityJSON export"""
    self.layout.operator(ImportCityJSON.bl_idname, text="CityJSON (.json)")


def register() -> None:
    """Registers the classes and functions of the addon"""

    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.cityjsonfy_properties = bpy.props.PointerProperty(
        type=prop.Up3dateCityJSONfyProperties
    )
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister() -> None:
    """Unregisters the classes and functions of the addon"""

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.cityjsonfy_properties


if __name__ == "__main__":
    register()
