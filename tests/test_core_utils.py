"""Unit tests for Blender-facing utility functions using lightweight fakes."""

from types import SimpleNamespace

import bpy
import pytest

from Up3date.core import utils
from Up3date.models.city_objects import GenericCityObject
from Up3date.models.cityjson import CityJSONDocument
from Up3date.models.geomprimitives import GeometrySemantics, MultiSurface


class PropertyBag(dict):
    """Dictionary with the custom-property behaviour used by Blender objects."""


class IdentityMatrix:
    def __matmul__(self, vector):
        return vector


class RemovableList(list):
    def remove(self, value, **_kwargs):
        super().remove(value)


@pytest.fixture(autouse=True)
def blender_state():
    bpy.context.scene = SimpleNamespace(
        world=PropertyBag(),
        collection=SimpleNamespace(children=SimpleNamespace(link=lambda _value: None)),
    )
    bpy.data.objects = []
    bpy.data.collections = []


def test_clean_list_and_assign_properties():
    assert utils.clean_list([[[1, 2]]]) == [1, 2]

    target = PropertyBag()
    result = utils.assign_properties(
        target,
        {
            "type": "Building",
            "attributes": {"height": 12, "nested": {"name": "tower"}},
            "geometry": ["ignored"],
            "children": ["ignored"],
        },
    )

    assert result is target
    assert target == {
        "type": "Building",
        "attributes.height": 12,
        "attributes.nested.name": "tower",
    }


def test_blender_safe_name_preserves_cityjson_identifiers_without_numeric_suffixes():
    assert utils.blender_safe_name("building-1") == "building-1"
    assert (
        utils.blender_safe_name("NL.IMBAG.Pand.0503100000000010")
        == "NL.IMBAG.Pand_0503100000000010"
    )


def test_remove_scene_objects_clears_world_objects_and_collections():
    bpy.context.scene.world.update({"CRS": "EPSG:7415", "transformed": True})
    bpy.data.objects = RemovableList([object(), object()])
    bpy.data.collections = RemovableList([object(), object()])

    utils.remove_scene_objects()

    assert bpy.context.scene.world == {}
    assert bpy.data.objects == []
    assert bpy.data.collections == []


def test_coordinate_translation_round_trip():
    vertices = [(10, 20, 30), (15, 18, 40)]

    translated, offx, offy, offz = utils.coord_translate_axis_origin(vertices)

    assert translated == ((0, 2, 0), (5, 0, 10))
    assert (offx, offy, offz) == (10, 18, 30)
    assert utils.original_coordinates(translated, offx, offy, offz) == tuple(vertices)
    assert utils.coord_translate_by_offset(vertices, 5, 10, 15)[0] == (
        (5, 10, 15),
        (10, 8, 25),
    )


def test_clean_buffer_and_geometry_names():
    vertices = ["unused", "a", "b", "c"]

    assert utils.clean_buffer(vertices, [(1, 3), (2,)]) == (
        ["a", "c", "b"],
        [(0, 1), (2,)],
    )
    assert (
        utils.get_geometry_name(
            "building-1", SimpleNamespace(type="MultiSurface", lod="2"), 3
        )
        == "3: [LoD2] building-1"
    )
    assert (
        utils.get_geometry_name("tree-1", SimpleNamespace(type="GeometryInstance"), 0)
        == "0: [GeometryInstance] tree-1"
    )


def test_bbox_combines_objects_and_restores_axis_translation():
    bpy.context.scene.world.update(
        {
            "Axis_Origin_X_translation": -10,
            "Axis_Origin_Y_translation": -20,
            "Axis_Origin_Z_translation": -30,
        }
    )
    objects = [
        SimpleNamespace(bound_box=[(-1, -2, -3), (2, 3, 4)]),
        SimpleNamespace(bound_box=[(-5, 0, 1), (1, 8, 9)]),
    ]

    assert utils.bbox(objects) == ([5, 18, 27], [12, 28, 39])


@pytest.mark.parametrize(
    ("world", "expected"),
    [
        ({}, [1, 2, 3]),
        (
            {
                "Axis_Origin_X_translation": -10,
                "Axis_Origin_Y_translation": -20,
                "Axis_Origin_Z_translation": -30,
            },
            [11, 22, 33],
        ),
        (
            {
                "transformed": True,
                "Axis_Origin_X_translation": -10,
                "Axis_Origin_Y_translation": -20,
                "Axis_Origin_Z_translation": -30,
                "transform.X_translate": 1,
                "transform.Y_translate": 2,
                "transform.Z_translate": 3,
                "transform.X_scale": 2,
                "transform.Y_scale": 2,
                "transform.Z_scale": 2,
            },
            [5, 10, 15],
        ),
    ],
)
def test_write_vertices_to_cityjson(world, expected):
    bpy.context.scene.world.update(world)
    city_object = SimpleNamespace(matrix_world=IdentityMatrix())
    doc = CityJSONDocument()

    utils.write_vertices_to_cityjson(city_object, (1, 2, 3), doc)

    assert doc.vertices == [expected]


def test_remove_vertex_duplicates_updates_geometry_indices():
    geometry = MultiSurface(lod="1", boundaries=[[[0, 1, 2, 3]]])
    doc = CityJSONDocument(
        city_objects={"building": GenericCityObject(geometry=[geometry])},
        vertices=[[0, 0, 0], [1, 0, 0], [1.0004, 0, 0], [0, 0, 0]],
    )

    removed = utils.remove_vertex_duplicates(doc, precision=3)

    assert removed == 2
    assert doc.vertices == [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    assert geometry.boundaries == [[[0, 1, 1, 0]]]


def test_remove_vertex_duplicates_uses_integer_precision_for_transformed_data():
    geometry = MultiSurface(lod="1", boundaries=[[[0, 1, 2]]])
    doc = CityJSONDocument(
        transform=utils.Transform(scale=[0.1, 0.1, 0.1], translate=[0, 0, 0]),
        city_objects={"building": GenericCityObject(geometry=[geometry])},
        vertices=[[0, 0, 0], [0.4, 0, 0], [1, 0, 0]],
    )

    removed = utils.remove_vertex_duplicates(doc, precision=8)

    assert removed == 1
    assert doc.vertices == [[0, 0, 0], [1, 0, 0]]
    assert geometry.boundaries == [[[0, 0, 1]]]


def test_export_transformation_parameters():
    bpy.context.scene.world.update(
        {
            "transformed": True,
            "transform.X_scale": 0.1,
            "transform.Y_scale": 0.2,
            "transform.Z_scale": 0.3,
            "transform.X_translate": 10,
            "transform.Y_translate": 20,
            "transform.Z_translate": 30,
        }
    )
    doc = CityJSONDocument()

    utils.export_transformation_parameters(doc)

    assert doc.transform is not None
    assert doc.transform.scale == [0.1, 0.2, 0.3]
    assert doc.transform.translate == [10, 20, 30]


def test_semantic_surfaces_are_stored_and_linked():
    geometry = MultiSurface(
        lod="1", semantics=GeometrySemantics(surfaces=[], values=[[]])
    )
    doc = CityJSONDocument(
        city_objects={"building": GenericCityObject(geometry=[geometry])}
    )
    wall = PropertyBag(type="WallSurface")
    wall.name = "Wall"
    invalid = PropertyBag(type=123)
    invalid.name = "Invalid"
    city_object = SimpleNamespace(data=SimpleNamespace(materials=[wall, None, invalid]))

    lookup = utils.store_semantic_surfaces(doc, city_object, 0, "building")
    utils.link_face_semantic_surface(
        doc,
        city_object,
        0,
        "building",
        lookup,
        SimpleNamespace(material_index=0),
    )
    utils.link_face_semantic_surface(
        doc,
        city_object,
        0,
        "building",
        lookup,
        SimpleNamespace(material_index=1),
    )

    assert lookup == {"Wall": 0}
    assert [surface.type for surface in geometry.semantics.surfaces] == ["WallSurface"]
    assert geometry.semantics.values == [[0, None]]


def test_semantic_helpers_ignore_objects_without_materials():
    city_object = SimpleNamespace(data=SimpleNamespace(materials=[]))
    doc = CityJSONDocument()

    assert utils.store_semantic_surfaces(doc, city_object, 0, "missing") is None
    assert (
        utils.link_face_semantic_surface(
            doc, city_object, 0, "missing", None, SimpleNamespace(material_index=0)
        )
        is None
    )


def test_export_metadata_uses_world_crs_and_scene_bounds():
    bpy.context.scene.world["CRS"] = "https://example.test/crs"
    bpy.data.objects = [
        SimpleNamespace(bound_box=[(0, 1, 2), (3.1234, 4.5678, 5.9999)])
    ]
    doc = CityJSONDocument()

    utils.export_metadata(doc)

    assert doc.metadata is not None
    assert doc.metadata.reference_system == "https://example.test/crs"
    assert doc.metadata.geographical_extent == [0, 1, 2, 3.123, 4.568, 6.0]


def test_export_parent_child_avoids_duplicates():
    parent = SimpleNamespace(
        name="parent", parent=None, type="EMPTY", get=lambda _key: None
    )
    child = SimpleNamespace(
        name="child", parent=parent, type="EMPTY", get=lambda _key: None
    )
    bpy.data.objects = [parent, child]
    parent_model = GenericCityObject(children=["child"])
    child_model = GenericCityObject()
    doc = CityJSONDocument(city_objects={"parent": parent_model, "child": child_model})

    utils.export_parent_child(doc)
    utils.export_parent_child(doc)

    assert parent_model.children == ["child"]
    assert child_model.parents == ["parent"]
