"""Module to manipulate materials in Blender regarding CityJSON

This module provides a set of factory classes to create materials
based on the semantics of the CityJSON file.
"""

from typing import ClassVar

import bpy

from .utils import assign_properties, clean_list


class BasicMaterialFactory:
    """A factory that creates a simple material for every city object"""

    material_colors: ClassVar[dict[str, tuple[float, float, float, float]]] = {
        "WallSurface": (0.8, 0.8, 0.8, 1.0),
        "RoofSurface": (0.9, 0.057, 0.086, 1.0),
        "GroundSurface": (0.507, 0.233, 0.036, 1.0),
    }

    default_color = (0, 0, 0, 1)

    def get_surface_color(self, surface_type):
        """Returns the material color of the appropriate surface type"""

        if surface_type in self.material_colors:
            return self.material_colors[surface_type]

        return self.default_color

    def create_material(self, surface):
        """Returns a new material based on the semantic surface of the object"""
        mat = bpy.data.materials.new(name=surface["type"])

        assign_properties(mat, surface)

        mat.diffuse_color = self.get_surface_color(surface["type"])

        return mat

    def get_material(self, surface):
        """Returns the material that corresponds to the semantic surface"""

        return self.create_material(surface)

    def get_materials(self, geometry=None, **params):
        """Returns the materials and material index list for the given
        geometry
        """
        mats = []
        values = []
        if "semantics" in geometry:
            values = geometry["semantics"]["values"]

            for surface in geometry["semantics"]["surfaces"]:
                mats.append(self.get_material(surface))

            values = clean_list(values)

        return mats, values


class ReuseMaterialFactory(BasicMaterialFactory):
    """A class that re-uses a material with similar semantics"""

    @staticmethod
    def check_material(material, surface):
        """Checks if the material can represent the provided surface"""

        if not material.name.startswith(surface["type"]):  # noqa: SIM103
            return False

        # TODO: Add logic here to check for semantic surface attributes

        return True

    def get_material(self, surface):
        """Returns the material that corresponds to the semantic surface"""

        matches = [m for m in bpy.data.materials if self.check_material(m, surface)]

        if matches:
            return matches[0]

        return self.create_material(surface)


class CityObjectTypeMaterialFactory:
    """A class that returns a material based on the object type"""

    type_color: ClassVar[dict[str, tuple[float, float, float, float]]] = {
        "Building": (0.9, 0.057, 0.086, 1.0),
        "BuildingPart": (0.9, 0.057, 0.086, 1.0),
        "BuildingInstallation": (0.9, 0.057, 0.086, 1.0),
        "Road": (0.4, 0.4, 0.4, 1.0),
        "LandUse": (242 / 255, 193 / 255, 25 / 255, 1.0),
        "PlantCover": (145 / 255, 191 / 255, 102 / 255, 1.0),
        "SolitaryVegetationObject": (145 / 255, 191 / 255, 102 / 255, 1.0),
        "TINRelief": (242 / 255, 193 / 255, 25 / 255, 1.0),
        "WaterBody": (54 / 255, 197 / 255, 214 / 255, 1.0),
    }

    default_color = (0.3, 0.3, 0.3, 1)

    @staticmethod
    def create_material(name, color):
        """Returns a new material based on the semantic surface of the object"""
        mat = bpy.data.materials.new(name=name)

        mat.diffuse_color = color

        return mat

    def get_type_color(self, object_type):
        """Returns the color that corresponds to the provided city object type"""

        if object_type in self.type_color:
            return self.type_color[object_type]

        return self.default_color

    def get_material(self, object_type):
        """Returns the material that corresponds to the provided
        object type
        """

        if object_type in bpy.data.materials:
            return bpy.data.materials[object_type]

        return self.create_material(object_type, self.get_type_color(object_type))

    def get_materials(self, cityobject=None, **params):
        """Returns the materials and material index list for the given
        geometry
        """

        return ([self.get_material(cityobject["type"])], [])
