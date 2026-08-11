"""Module to manipulate materials in Blender regarding CityJSON

This module provides a set of factory classes to create materials
based on the semantics of the CityJSON file.
"""

from typing import ClassVar, Protocol, cast

import bpy

from ..models.geomprimitives import GeometryPrimitive, Semantics
from .blender_types import BlenderMaterial
from .cityjson_utils import clean_list
from .scene import assign_properties

Color = tuple[float, float, float, float]


class TypedCityObject(Protocol):
    type: str


class BasicMaterialFactory:
    """A factory that creates a simple material for every city object"""

    material_colors: ClassVar[dict[str, tuple[float, float, float, float]]] = {
        "WallSurface": (0.8, 0.8, 0.8, 1.0),
        "RoofSurface": (0.9, 0.057, 0.086, 1.0),
        "GroundSurface": (0.507, 0.233, 0.036, 1.0),
    }

    default_color: ClassVar[Color] = (0, 0, 0, 1)

    def get_surface_color(self, surface_type: str) -> Color:
        """Returns the material color of the appropriate surface type"""

        if surface_type in self.material_colors:
            return self.material_colors[surface_type]

        return self.default_color

    def create_material(self, surface: Semantics) -> BlenderMaterial:
        """Returns a new material based on the semantic surface of the object"""
        mat = bpy.data.materials.new(name=surface.type)

        assign_properties(mat, surface.to_dict())

        mat.diffuse_color = self.get_surface_color(surface.type)

        return mat

    def get_material(self, surface: Semantics) -> BlenderMaterial:
        """Returns the material that corresponds to the semantic surface"""

        return self.create_material(surface)

    def get_materials(
        self,
        geometry: GeometryPrimitive | None = None,
        city_object: TypedCityObject | None = None,
    ) -> tuple[list[BlenderMaterial], list[int | None]]:
        """Returns the materials and material index list for the given
        geometry
        """
        mats: list[BlenderMaterial] = []
        values: list[int | None] = []
        if geometry is None:
            return mats, values
        semantics = getattr(geometry, "semantics", None)
        if semantics is not None:
            values = cast(list[int | None], semantics.values)

            for surface in semantics.surfaces:
                mats.append(self.get_material(surface))

            values = cast(list[int | None], clean_list(values))

        return mats, values


class ReuseMaterialFactory(BasicMaterialFactory):
    """A class that re-uses a material with similar semantics"""

    @staticmethod
    def check_material(material: BlenderMaterial, surface: Semantics) -> bool:
        """Checks if the material can represent the provided surface"""

        if not material.name.startswith(surface.type):
            return False

        return material.get("type") == surface.type

    def get_material(self, surface: Semantics) -> BlenderMaterial:
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

    default_color: ClassVar[Color] = (0.3, 0.3, 0.3, 1)

    @staticmethod
    def create_material(name: str, color: Color) -> BlenderMaterial:
        """Returns a new material based on the semantic surface of the object"""
        mat = bpy.data.materials.new(name=name)

        mat.diffuse_color = color

        return mat

    def get_type_color(self, object_type: str) -> Color:
        """Returns the color that corresponds to the provided city object type"""

        if object_type in self.type_color:
            return self.type_color[object_type]

        return self.default_color

    def get_material(self, object_type: str) -> BlenderMaterial:
        """Returns the material that corresponds to the provided
        object type
        """

        if object_type in bpy.data.materials:
            return bpy.data.materials[object_type]

        return self.create_material(object_type, self.get_type_color(object_type))

    def get_materials(
        self,
        geometry: GeometryPrimitive | None = None,
        city_object: TypedCityObject | None = None,
    ) -> tuple[list[BlenderMaterial], list[int | None]]:
        """Returns the materials and material index list for the given
        geometry
        """

        if city_object is None:
            return ([], [])
        return ([self.get_material(city_object.type)], [])
