"""Unit tests for core material factories without a Blender process."""

from types import SimpleNamespace

import bpy
import pytest

from Up3date.core.material import (
    BasicMaterialFactory,
    CityObjectTypeMaterialFactory,
    ReuseMaterialFactory,
)
from Up3date.models.geomprimitives import GeometrySemantics, MultiSurface, Semantics


class FakeMaterial(dict):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.diffuse_color = None


class MaterialStore(list):
    def new(self, name):
        material = FakeMaterial(name)
        self.append(material)
        return material

    def __contains__(self, value):
        if isinstance(value, str):
            return any(material.name == value for material in self)
        return super().__contains__(value)

    def __getitem__(self, value):
        if isinstance(value, str):
            return next(material for material in self if material.name == value)
        return super().__getitem__(value)


@pytest.fixture(autouse=True)
def material_store():
    bpy.data.materials = MaterialStore()
    return bpy.data.materials


def test_basic_material_factory_creates_surface_material():
    factory = BasicMaterialFactory()
    surface = Semantics(type="RoofSurface", extra={"slope": 30})

    material = factory.get_material(surface)

    assert material.name == "RoofSurface"
    assert material["type"] == "RoofSurface"
    assert material["slope"] == 30
    assert material.diffuse_color == (0.9, 0.057, 0.086, 1.0)
    assert factory.get_surface_color("UnknownSurface") == factory.default_color


def test_basic_material_factory_flattens_semantic_values():
    geometry = MultiSurface(
        lod="2",
        semantics=GeometrySemantics(
            surfaces=[Semantics(type="WallSurface"), Semantics(type="RoofSurface")],
            values=[[0, 1]],
        ),
    )

    materials, values = BasicMaterialFactory().get_materials(geometry=geometry)

    assert [material.name for material in materials] == [
        "WallSurface",
        "RoofSurface",
    ]
    assert values == [0, 1]
    assert BasicMaterialFactory().get_materials() == ([], [])


def test_reuse_material_factory_reuses_matching_material(material_store):
    existing = material_store.new("WallSurface.001")
    existing["type"] = "WallSurface"
    factory = ReuseMaterialFactory()

    assert factory.get_material(Semantics(type="WallSurface")) is existing
    assert not factory.check_material(existing, Semantics(type="RoofSurface"))


def test_reuse_material_factory_rejects_untagged_blender_material(material_store):
    existing = material_store.new("WallSurface")

    material = ReuseMaterialFactory().get_material(Semantics(type="WallSurface"))

    assert material is not existing
    assert material["type"] == "WallSurface"


def test_reuse_material_factory_creates_material_without_match(material_store):
    material = ReuseMaterialFactory().get_material(Semantics(type="GroundSurface"))

    assert material.name == "GroundSurface"
    assert material in material_store
    assert material["type"] == "GroundSurface"


def test_city_object_type_material_factory_reuses_type_material(material_store):
    factory = CityObjectTypeMaterialFactory()
    existing = material_store.new("Building")

    assert factory.get_material("Building") is existing
    road = factory.get_material("Road")
    assert road.diffuse_color == (0.4, 0.4, 0.4, 1.0)
    assert factory.get_type_color("UnknownType") == factory.default_color
    assert factory.get_materials(city_object=SimpleNamespace(type="Road")) == (
        [road],
        [],
    )
    assert factory.get_materials() == ([], [])
