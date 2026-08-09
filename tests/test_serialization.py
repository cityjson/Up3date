"""Full round-trip serialization tests for CityJSON 2.0.2 models."""

import json

import pytest

from models.cityjson import CityJSONDocument
from models.cityobjects import (
    Building,
    CityObjectGroup,
    ExtensionObject,
    Road,
    Tunnel,
    cityobject_from_dict,
)
from models.geomprimitives import (
    CompositeSolid,
    MultiSurface,
    Solid,
    geom_primitive_from_dict,
)
from models.geomtemplates import GeometryInstance


# ---------------------------------------------------------------------------
# Geometry primitive round-trips
# ---------------------------------------------------------------------------

class TestGeomRoundTrips:
    def test_multi_surface_no_extras(self):
        raw = {"type": "MultiSurface", "lod": "1", "boundaries": [[[[0, 1, 2, 3]]]]}
        assert geom_primitive_from_dict(raw).to_dict() == raw

    def test_solid_with_two_shells(self):
        raw = {
            "type": "Solid",
            "lod": "2",
            "boundaries": [
                [[[0, 1, 2, 3]], [[4, 5, 6, 7]]],  # shell 1
            ],
        }
        assert geom_primitive_from_dict(raw).to_dict() == raw

    def test_composite_solid_deep_nesting(self):
        raw = {
            "type": "CompositeSolid",
            "lod": "3",
            "boundaries": [[[[[[0, 1, 2]]]]]],
        }
        assert geom_primitive_from_dict(raw).to_dict() == raw

    def test_multi_surface_with_all_optional_fields(self):
        raw = {
            "type": "MultiSurface",
            "lod": "2",
            "boundaries": [[[[0, 1, 2]]]],
            "semantics": {
                "surfaces": [{"type": "WallSurface", "parent": 1}],
                "values": [0],
            },
            "material": {"myTheme": {"value": 3}},
            "texture": {"texTheme": {"values": [[[0, 1]]]}},
        }
        result = geom_primitive_from_dict(raw).to_dict()
        assert result == raw


# ---------------------------------------------------------------------------
# GeometryInstance round-trip
# ---------------------------------------------------------------------------

class TestGeometryInstanceRoundTrip:
    def test_roundtrip(self):
        raw = {
            "type": "GeometryInstance",
            "template": 0,
            "boundaries": [4],
            "transformationMatrix": [
                1.0, 0.0, 0.0, 10.0,
                0.0, 1.0, 0.0, 20.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
        }
        assert GeometryInstance.from_dict(raw).to_dict() == raw


# ---------------------------------------------------------------------------
# CityObject round-trips
# ---------------------------------------------------------------------------

class TestCityObjectRoundTrips:
    def test_building_minimal(self):
        raw = {"type": "Building", "geometry": []}
        result = cityobject_from_dict(raw).to_dict()
        assert result["type"] == "Building"
        assert "geometry" in result

    def test_building_full(self):
        raw = {
            "type": "Building",
            "attributes": {"measuredHeight": 10.5, "roofType": "Flat"},
            "parents": ["p1"],
            "children": ["c1"],
            "geographicalExtent": [0.0, 0.0, 0.0, 10.0, 10.0, 15.0],
            "geometry": [
                {
                    "type": "MultiSurface",
                    "lod": "2",
                    "boundaries": [[[[0, 1, 2, 3]]]],
                }
            ],
        }
        result = cityobject_from_dict(raw).to_dict()
        assert result["type"] == "Building"
        assert result["attributes"] == {"measuredHeight": 10.5, "roofType": "Flat"}
        assert result["children"] == ["c1"]
        assert result["geometry"][0]["type"] == "MultiSurface"

    def test_building_with_address(self):
        raw = {
            "type": "Building",
            "address": [
                {"location": {"type": "MultiPoint", "lod": "0", "boundaries": [0]}}
            ],
            "geometry": [],
        }
        result = cityobject_from_dict(raw).to_dict()
        assert "address" in result
        assert result["address"][0]["location"]["type"] == "MultiPoint"

    def test_city_object_group_with_members(self):
        # Per spec §2.5, group members are stored in "children"
        raw = {
            "type": "CityObjectGroup",
            "children": ["b1", "b2", "t1"],
            "geometry": [],
        }
        result = cityobject_from_dict(raw).to_dict()
        assert result["children"] == ["b1", "b2", "t1"]

    def test_extension_object_preserved(self):
        raw = {"type": "+MyCustomType"}
        result = cityobject_from_dict(raw).to_dict()
        assert result["type"] == "+MyCustomType"

    def test_road_with_multi_line_string(self):
        raw = {
            "type": "Road",
            "geometry": [
                {"type": "MultiLineString", "lod": "0", "boundaries": [[0, 1, 2]]}
            ],
        }
        result = cityobject_from_dict(raw).to_dict()
        assert result["geometry"][0]["type"] == "MultiLineString"


# ---------------------------------------------------------------------------
# Full CityJSONDocument round-trips
# ---------------------------------------------------------------------------

class TestDocumentRoundTrips:
    def test_minimal_roundtrip(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        result = doc.to_dict()

        assert result["type"] == "CityJSON"
        assert result["version"] == "2.0"
        assert result["vertices"] == minimal_dict["vertices"]
        assert result["transform"]["scale"] == minimal_dict["transform"]["scale"]
        assert result["transform"]["translate"] == minimal_dict["transform"]["translate"]
        assert result["metadata"]["referenceSystem"] == minimal_dict["metadata"]["referenceSystem"]
        assert "building-1" in result["CityObjects"]
        assert result["CityObjects"]["building-1"]["type"] == "Building"

    def test_no_transform_roundtrip(self):
        raw = {
            "type": "CityJSON",
            "version": "2.0",
            "CityObjects": {
                "r1": {"type": "Road", "geometry": []}
            },
            "vertices": [],
        }
        result = CityJSONDocument.from_dict(raw).to_dict()
        assert "transform" not in result
        assert result["CityObjects"]["r1"]["type"] == "Road"

    def test_geometry_templates_roundtrip(self, templates_dict):
        doc = CityJSONDocument.from_dict(templates_dict)
        result = doc.to_dict()
        assert "geometry-templates" in result
        assert result["geometry-templates"]["vertices-templates"] == templates_dict["geometry-templates"]["vertices-templates"]

    def test_appearance_roundtrip(self, appearance_dict):
        doc = CityJSONDocument.from_dict(appearance_dict)
        result = doc.to_dict()
        assert "appearance" in result
        assert "vertices-texture" in result["appearance"]
        assert result["appearance"]["default-theme-texture"] == "myTheme"
        assert result["appearance"]["default-theme-material"] == "myMatTheme"

    def test_json_serializable(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        # Should not raise
        json_str = json.dumps(doc.to_dict())
        parsed = json.loads(json_str)
        assert parsed["version"] == "2.0"

    def test_solid_geometry_roundtrip(self, solid_dict):
        doc = CityJSONDocument.from_dict(solid_dict)
        result = doc.to_dict()
        geom = result["CityObjects"]["tunnel-1"]["geometry"][0]
        assert geom["type"] == "Solid"
        assert len(geom["boundaries"]) == 1  # one shell


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_unknown_cityobject_type_raises(self):
        raw = {
            "type": "CityJSON",
            "version": "2.0",
            "CityObjects": {"x": {"type": "UFO", "geometry": []}},
            "vertices": [],
        }
        with pytest.raises(ValueError, match="Unknown CityObject type"):
            CityJSONDocument.from_dict(raw)

    def test_unknown_geometry_type_raises(self):
        from models.geomprimitives import geom_primitive_from_dict
        with pytest.raises(ValueError, match="Unknown geometry type"):
            geom_primitive_from_dict({"type": "HyperCube", "lod": "0", "boundaries": []})

    def test_missing_transform_is_none(self):
        raw = {"type": "CityJSON", "version": "2.0", "CityObjects": {}, "vertices": []}
        doc = CityJSONDocument.from_dict(raw)
        assert doc.transform is None

    def test_missing_metadata_is_none(self):
        raw = {"type": "CityJSON", "version": "2.0", "CityObjects": {}, "vertices": []}
        doc = CityJSONDocument.from_dict(raw)
        assert doc.metadata is None


# ---------------------------------------------------------------------------
# LoD string format
# ---------------------------------------------------------------------------

class TestLodFormat:
    @pytest.mark.parametrize("lod", ["0", "1", "2", "3", "0.0", "1.2", "2.3", "3.3"])
    def test_valid_lod_strings(self, lod):
        raw = {"type": "MultiSurface", "lod": lod, "boundaries": []}
        obj = geom_primitive_from_dict(raw)
        assert obj.lod == lod
        assert isinstance(obj.lod, str)

    def test_lod_preserved_in_document(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        geom = doc.to_dict()["CityObjects"]["building-1"]["geometry"][0]
        assert geom["lod"] == "1"
        assert isinstance(geom["lod"], str)
