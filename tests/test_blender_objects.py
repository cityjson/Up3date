"""Tests for CityJSON importer/exporter orchestration at the Blender boundary."""

import json
from types import SimpleNamespace

import bpy
import idprop
import pytest

from Up3date.blender import exporter, importer
from Up3date.blender.material import (
    BasicMaterialFactory,
    CityObjectTypeMaterialFactory,
    ReuseMaterialFactory,
)
from Up3date.models.city_objects import Building, GenericCityObject
from Up3date.models.cityjson import CityJSONDocument, Transform
from Up3date.models.geomprimitives import MultiSurface


class FakeBlenderObject(dict):
    def __init__(self, name="object", **properties):
        super().__init__(properties)
        self.name = name
        self.data = SimpleNamespace(materials=[], vertices=[], polygons=[])


@pytest.fixture(autouse=True)
def blender_state():
    bpy.context.scene = SimpleNamespace(world={})


@pytest.mark.parametrize(
    ("material_type", "reuse", "expected_factory"),
    [
        ("SURFACES", True, ReuseMaterialFactory),
        ("SURFACES", False, BasicMaterialFactory),
        ("CITY_OBJECTS", True, CityObjectTypeMaterialFactory),
    ],
)
def test_parser_selects_material_factory(material_type, reuse, expected_factory):
    parser = importer.CityJSONImporter("city.json", material_type, reuse)

    assert isinstance(parser.material_factory, expected_factory)


def test_prepare_vertices_translates_untransformed_document_to_origin():
    parser = importer.CityJSONImporter("city.json", "CITY_OBJECTS")
    parser.document = CityJSONDocument(vertices=[[5, 4, 3], [8, 10, 12]])

    parser.prepare_vertices()

    assert parser.vertices == ((0.0, 0.0, 0.0), (3.0, 6.0, 9.0))
    assert bpy.context.scene.world == {
        "Axis_Origin_X_translation": -5.0,
        "Axis_Origin_Y_translation": -4.0,
        "Axis_Origin_Z_translation": -3.0,
    }


def test_prepare_vertices_applies_cityjson_transform():
    parser = importer.CityJSONImporter("city.json", "CITY_OBJECTS")
    parser.document = CityJSONDocument(
        transform=Transform(scale=[2, 3, 4], translate=[10, 20, 30]),
        vertices=[[1, 2, 3], [2, 4, 5]],
    )

    parser.prepare_vertices()

    assert parser.vertices == ((0, 0, 0), (2, 6, 8))
    assert bpy.context.scene.world["transformed"] is True
    assert bpy.context.scene.world["transform.Y_scale"] == 3
    assert bpy.context.scene.world["transform.Z_translate"] == 30


def test_prepare_vertices_reuses_existing_axis_translation():
    bpy.context.scene.world.update(
        {
            "Axis_Origin_X_translation": -10,
            "Axis_Origin_Y_translation": -20,
            "Axis_Origin_Z_translation": -30,
        }
    )
    parser = importer.CityJSONImporter("city.json", "CITY_OBJECTS")
    parser.document = CityJSONDocument(vertices=[[12, 23, 34]])

    parser.prepare_vertices()

    assert parser.vertices == ((2.0, 3.0, 4.0),)


def test_prepare_vertices_requires_loaded_document():
    parser = importer.CityJSONImporter("city.json", "CITY_OBJECTS")

    with pytest.raises(RuntimeError, match="must be loaded"):
        parser.prepare_vertices()


def test_load_data_deserializes_cityjson(tmp_path):
    input_path = tmp_path / "minimal.city.json"
    input_path.write_text(
        json.dumps(
            {"type": "CityJSON", "version": "2.0", "CityObjects": {}, "vertices": []}
        )
    )
    parser = importer.CityJSONImporter(str(input_path), "CITY_OBJECTS")

    parser.load_data()

    assert parser.data["version"] == "2.0"
    assert parser.document is not None
    assert parser.document.city_objects == {}


def test_parse_geometry_builds_mesh_and_properties(monkeypatch):
    parser = importer.CityJSONImporter("city.json", "CITY_OBJECTS")
    parser.vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    parser.material_factory = SimpleNamespace(
        get_materials=lambda **_kwargs: (["material"], [0])
    )
    created = FakeBlenderObject()
    captured = {}

    def create_mesh_object(name, vertices, faces, materials, material_indices):
        captured.update(
            name=name,
            vertices=vertices,
            faces=faces,
            materials=materials,
            material_indices=material_indices,
        )
        return created

    monkeypatch.setattr(importer, "create_mesh_object", create_mesh_object)
    geometry = MultiSurface(lod="2", boundaries=[[[0, 1, 2]]])

    result = parser.parse_geometry(
        "building-1", SimpleNamespace(type="Building"), geometry, 0
    )

    assert result is created
    assert captured == {
        "name": "0: [LoD2] building-1",
        "vertices": [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
        "faces": [(0, 1, 2)],
        "materials": ["material"],
        "material_indices": [0],
    }
    assert created == {"lod": "2", "type": "MultiSurface"}


def test_exporter_creates_typed_city_object_from_custom_properties():
    city_object = FakeBlenderObject(
        type="Building",
        **{
            "attributes.height": 12,
            "attributes.address.city": "Delft",
            "children": idprop.types.IDPropertyArray(["part-1"]),
            "_RNA_UI": "ignored",
        },
    )
    doc = CityJSONDocument()

    exporter.CityJSONExporter.get_custom_properties(city_object, doc, "building-1")

    result = doc.city_objects["building-1"]
    assert isinstance(result, Building)
    assert result.attributes == {"height": 12, "address": {"city": "Delft"}}
    assert result.children == ["part-1"]


def test_exporter_preserves_existing_geometry_and_relationships():
    geometry = MultiSurface(lod="1")
    doc = CityJSONDocument(
        city_objects={"building-1": GenericCityObject(geometry=[geometry])}
    )
    city_object = FakeBlenderObject(
        type="Building",
        parents=["parent"],
        geographicalExtent=[0, 0, 0, 1, 1, 1],
    )

    exporter.CityJSONExporter.get_custom_properties(city_object, doc, "building-1")

    result = doc.city_objects["building-1"]
    assert isinstance(result, Building)
    assert result.geometry == [geometry]
    assert result.parents == ["parent"]
    assert result.geographical_extent == [0, 0, 0, 1, 1, 1]


def test_create_mesh_structure_adds_geometry_and_semantics():
    city_object = FakeBlenderObject(name="mesh", lod="1", type="MultiSurface")
    city_object.data.materials = ["wall"]
    doc = CityJSONDocument()

    city_object_id, vertices, polygons = (
        exporter.CityJSONExporter.create_mesh_structure(
            city_object, "0: [LoD1] building-1", doc
        )
    )

    assert city_object_id == "building-1"
    assert vertices == []
    assert polygons == []
    model = doc.city_objects[city_object_id]
    assert isinstance(model, GenericCityObject)
    assert model.geometry[0].lod == "1"
    assert model.geometry[0].semantics is not None


@pytest.mark.parametrize(
    "properties",
    [
        {"type": "MultiSurface"},
        {"lod": "1", "type": "MultiSolid"},
    ],
)
def test_create_mesh_structure_rejects_invalid_properties(properties):
    city_object = FakeBlenderObject(name="invalid", **properties)

    with pytest.raises(SystemExit):
        exporter.CityJSONExporter.create_mesh_structure(
            city_object, "0: [LoD1] building-1", CityJSONDocument()
        )


def test_export_geometry_and_semantics_writes_multi_surface(monkeypatch):
    geometry = MultiSurface(lod="1")
    doc = CityJSONDocument(
        city_objects={"building-1": GenericCityObject(geometry=[geometry])}
    )
    city_object = FakeBlenderObject(type="MultiSurface")
    city_object.matrix_world = SimpleNamespace()
    vertices = [SimpleNamespace(co=(0, 0, 0)), SimpleNamespace(co=(1, 0, 0))]
    faces = [SimpleNamespace(index=0, vertices=[0, 1], material_index=0)]
    linked_faces = []

    monkeypatch.setattr(exporter, "store_semantic_surfaces", lambda *_args: {})
    monkeypatch.setattr(
        exporter,
        "write_vertices_to_cityjson",
        lambda _obj, vertex, target: target.vertices.append(list(vertex)),
    )
    monkeypatch.setattr(
        exporter,
        "link_face_semantic_surface",
        lambda *_args: linked_faces.append(_args[-1]),
    )

    next_index = exporter.CityJSONExporter.export_geometry_and_semantics(
        city_object, doc, "building-1", faces, vertices, {}, 0
    )

    assert next_index == 2
    assert geometry.boundaries == [[[0, 1]]]
    assert doc.vertices == [[0, 0, 0], [1, 0, 0]]
    assert linked_faces == faces


def test_initialize_document_returns_new_documents():
    first = exporter.CityJSONExporter.initialize_document()
    second = exporter.CityJSONExporter.initialize_document()

    assert isinstance(first, CityJSONDocument)
    assert first is not second
