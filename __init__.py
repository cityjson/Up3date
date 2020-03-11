"""Main module of the CityJSON Blender addon"""

import json
import time

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .core.objects import CityJSONParser, cityJSON_exporter

bl_info = {
    "name": "Import CityJSON files",
    "author": "Konstantinos Mastorakis",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > CityJSON (.json)",
    "description": "Visualize 3D City Models encoded in CityJSON format",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

class ImportCityJSON(Operator, ImportHelper):
    "Load a CityJSON file"
    bl_idname = "cityjson.import_file"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import CityJSON"

    # ImportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    material_type: EnumProperty(
        name="Materials' type",
        items=(('SURFACES', "Surfaces",
                "Creates materials based on semantic surface types"),
               ('CITY_OBJECTS', "City Objects",
                "Creates materials based on the type of city object")),
        description=(
            "Create materials based on city object or semantic"
            " surfaces."
        )
    )

    reuse_materials: BoolProperty(
        name="Reuse materials",
        description="Use common materials according to surface type",
        default=True
    )

    clean_scene: BoolProperty(
        name="Clean scene",
        description="Remove existing objects from the scene before importing",
        default=True
    )

    origin_text: BoolProperty(
        name="Insert origin",
        description="Insert a text displaying the coordinates of the origin",
        default=True
    )
        
    def execute(self, context):
        """Executes the import process"""

        parser = CityJSONParser(self.filepath,
                                material_type=self.material_type,
                                reuse_materials=self.reuse_materials,
                                clear_scene=self.clean_scene,
                                origin_text=self.origin_text)

        return parser.execute()

class ExportCityJSON(Operator, ExportHelper):
    "Export scene as a CityJSON file"
    bl_idname = "cityjson.export_file"
    bl_label = "Export CityJSON"

    # ExportHelper mixin class uses this
    filename_ext = ".json"

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return cityJSON_exporter(context, self.filepath)

classes = (
    ImportCityJSON,
    ExportCityJSON
)

def menu_func_export(self, context):
    """Defines the menu item for CityJSON import"""

    self.layout.operator(ExportCityJSON.bl_idname, text="CityJSON (.json)")

def menu_func_import(self, context):
    """Defines the menu item for CityJSON export"""
    self.layout.operator(ImportCityJSON.bl_idname, text="CityJSON (.json)")

def register():
    """Registers the classes and functions of the addon"""

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    """Unregisters the classes and functions of the addon"""

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
