"""Tests for models/geomprimitives.py — CityJSON 2.0.2 geometry primitives."""

import pytest

from models.geomprimitives import (
    GEOMPRIMITIVE_TYPES,
    CompositeSolid,
    CompositeSurface,
    GeometrySemantics,
    MaterialValue,
    MultiLineString,
    MultiPoint,
    MultiSolid,
    MultiSurface,
    Semantics,
    Solid,
    TextureTheme,
    geom_primitive_from_dict,
)


# ---------------------------------------------------------------------------
# Semantics
# ---------------------------------------------------------------------------

class TestSemantics:
    def test_basic(self):
        s = Semantics(type="WallSurface")
        assert s.type == "WallSurface"
        assert s.extra == {}

    def test_extra_fields(self):
        s = Semantics(type="WallSurface", extra={"parent": 0})
        assert s.extra["parent"] == 0

    def test_from_dict_basic(self):
        s = Semantics.from_dict({"type": "RoofSurface"})
        assert s.type == "RoofSurface"
        assert s.extra == {}

    def test_from_dict_extra(self):
        s = Semantics.from_dict({"type": "WallSurface", "parent": 1, "children": [2]})
        assert s.type == "WallSurface"
        assert s.extra == {"parent": 1, "children": [2]}

    def test_to_dict_roundtrip(self):
        raw = {"type": "GroundSurface", "parent": 0}
        assert Semantics.from_dict(raw).to_dict() == raw

    def test_to_dict_no_extra(self):
        assert Semantics(type="WallSurface").to_dict() == {"type": "WallSurface"}


# ---------------------------------------------------------------------------
# GeometrySemantics
# ---------------------------------------------------------------------------

class TestGeometrySemantics:
    def test_empty(self):
        gs = GeometrySemantics()
        assert gs.surfaces == []
        assert gs.values is None

    def test_from_dict(self):
        raw = {
            "surfaces": [{"type": "WallSurface"}, {"type": "RoofSurface"}],
            "values": [0, 1],
        }
        gs = GeometrySemantics.from_dict(raw)
        assert len(gs.surfaces) == 2
        assert gs.surfaces[0].type == "WallSurface"
        assert gs.values == [0, 1]

    def test_roundtrip(self):
        raw = {
            "surfaces": [{"type": "WallSurface", "parent": 1}],
            "values": [[0, None]],
        }
        gs = GeometrySemantics.from_dict(raw)
        assert gs.to_dict() == raw

    def test_null_values(self):
        raw = {"surfaces": [], "values": None}
        gs = GeometrySemantics.from_dict(raw)
        assert gs.values is None


# ---------------------------------------------------------------------------
# MaterialValue
# ---------------------------------------------------------------------------

class TestMaterialValue:
    def test_value_only(self):
        mv = MaterialValue.from_dict({"value": 3})
        assert mv.value == 3
        assert mv.values is None
        assert mv.to_dict() == {"value": 3}

    def test_values_only(self):
        mv = MaterialValue.from_dict({"values": [[0, 1], [None, 2]]})
        assert mv.value is None
        assert mv.to_dict() == {"values": [[0, 1], [None, 2]]}


# ---------------------------------------------------------------------------
# TextureTheme
# ---------------------------------------------------------------------------

class TestTextureTheme:
    def test_roundtrip(self):
        raw = {"values": [[[0, 1], None], [[2, 3]]]}
        tt = TextureTheme.from_dict(raw)
        assert tt.to_dict() == raw


# ---------------------------------------------------------------------------
# MultiPoint
# ---------------------------------------------------------------------------

class TestMultiPoint:
    def test_type_literal(self):
        mp = MultiPoint(lod="0", boundaries=[0, 1, 2])
        assert mp.type == "MultiPoint"

    def test_from_dict(self):
        raw = {"type": "MultiPoint", "lod": "0", "boundaries": [0, 1, 2]}
        mp = MultiPoint.from_dict(raw)
        assert mp.lod == "0"
        assert mp.boundaries == [0, 1, 2]
        assert mp.semantics is None

    def test_to_dict_roundtrip(self):
        raw = {"type": "MultiPoint", "lod": "1", "boundaries": [0]}
        assert MultiPoint.from_dict(raw).to_dict() == raw

    def test_no_material_texture(self):
        mp = MultiPoint(lod="0")
        assert not hasattr(mp, "material")
        assert not hasattr(mp, "texture")


# ---------------------------------------------------------------------------
# MultiLineString
# ---------------------------------------------------------------------------

class TestMultiLineString:
    def test_type_literal(self):
        mls = MultiLineString(lod="0")
        assert mls.type == "MultiLineString"

    def test_from_dict(self):
        raw = {"type": "MultiLineString", "lod": "1", "boundaries": [[0, 1], [2, 3]]}
        mls = MultiLineString.from_dict(raw)
        assert mls.boundaries == [[0, 1], [2, 3]]

    def test_roundtrip(self):
        raw = {"type": "MultiLineString", "lod": "0", "boundaries": [[0, 1, 2]]}
        assert MultiLineString.from_dict(raw).to_dict() == raw


# ---------------------------------------------------------------------------
# MultiSurface
# ---------------------------------------------------------------------------

class TestMultiSurface:
    def test_type_literal(self):
        ms = MultiSurface(lod="1")
        assert ms.type == "MultiSurface"

    def test_boundary_depth(self):
        ms = MultiSurface(lod="1", boundaries=[[[0, 1, 2, 3]]])
        assert isinstance(ms.boundaries[0], list)
        assert isinstance(ms.boundaries[0][0], list)

    def test_from_dict_with_semantics(self):
        raw = {
            "type": "MultiSurface",
            "lod": "2",
            "boundaries": [[[[0, 1, 2, 3]]], [[[4, 5, 6, 7]]]],
            "semantics": {
                "surfaces": [{"type": "WallSurface"}, {"type": "RoofSurface"}],
                "values": [0, 1],
            },
        }
        ms = MultiSurface.from_dict(raw)
        assert ms.semantics is not None
        assert len(ms.semantics.surfaces) == 2

    def test_from_dict_with_material(self):
        raw = {
            "type": "MultiSurface",
            "lod": "2",
            "boundaries": [[[[0, 1, 2]]]],
            "material": {"theme1": {"value": 0}},
        }
        ms = MultiSurface.from_dict(raw)
        assert ms.material is not None
        assert ms.material["theme1"].value == 0

    def test_roundtrip_minimal(self):
        raw = {"type": "MultiSurface", "lod": "1", "boundaries": [[[[0, 1, 2]]]]}
        assert MultiSurface.from_dict(raw).to_dict() == raw

    def test_roundtrip_with_all_fields(self):
        raw = {
            "type": "MultiSurface",
            "lod": "2",
            "boundaries": [[[[0, 1, 2]]]],
            "semantics": {
                "surfaces": [{"type": "WallSurface"}],
                "values": [0],
            },
            "material": {"default": {"value": 1}},
            "texture": {"myTheme": {"values": [[[0, 1], [2, 3]]]}},
        }
        result = MultiSurface.from_dict(raw).to_dict()
        assert result == raw


# ---------------------------------------------------------------------------
# CompositeSurface
# ---------------------------------------------------------------------------

class TestCompositeSurface:
    def test_type_literal(self):
        cs = CompositeSurface(lod="2")
        assert cs.type == "CompositeSurface"

    def test_roundtrip(self):
        raw = {"type": "CompositeSurface", "lod": "2", "boundaries": [[[[0, 1, 2]]]]}
        assert CompositeSurface.from_dict(raw).to_dict() == raw


# ---------------------------------------------------------------------------
# Solid
# ---------------------------------------------------------------------------

class TestSolid:
    def test_type_literal(self):
        s = Solid(lod="2")
        assert s.type == "Solid"

    def test_boundary_depth(self):
        s = Solid(lod="2", boundaries=[[[[0, 1, 2, 3]]]])
        # shell -> surfaces -> rings -> indices (4 levels)
        assert isinstance(s.boundaries[0], list)
        assert isinstance(s.boundaries[0][0], list)
        assert isinstance(s.boundaries[0][0][0], list)

    def test_from_dict(self):
        raw = {
            "type": "Solid",
            "lod": "2",
            "boundaries": [[[[0, 1, 2, 3]], [[4, 5, 6, 7]]]],
        }
        s = Solid.from_dict(raw)
        assert len(s.boundaries[0]) == 2  # two surfaces in one shell

    def test_roundtrip(self):
        raw = {"type": "Solid", "lod": "2", "boundaries": [[[[0, 1, 2, 3]]]]}
        assert Solid.from_dict(raw).to_dict() == raw


# ---------------------------------------------------------------------------
# CompositeSolid
# ---------------------------------------------------------------------------

class TestCompositeSolid:
    def test_type_literal(self):
        cs = CompositeSolid(lod="3")
        assert cs.type == "CompositeSolid"

    def test_boundary_depth(self):
        cs = CompositeSolid(lod="3", boundaries=[[[[[0, 1, 2]]]]])
        # solid -> shell -> surface -> ring -> indices (5 levels)
        assert isinstance(cs.boundaries[0][0][0][0], list)

    def test_roundtrip(self):
        raw = {"type": "CompositeSolid", "lod": "3", "boundaries": [[[[[0, 1, 2]]]]]}
        assert CompositeSolid.from_dict(raw).to_dict() == raw


# ---------------------------------------------------------------------------
# MultiSolid
# ---------------------------------------------------------------------------

class TestMultiSolid:
    def test_type_literal(self):
        ms = MultiSolid(lod="3")
        assert ms.type == "MultiSolid"

    def test_roundtrip(self):
        raw = {"type": "MultiSolid", "lod": "2", "boundaries": [[[[[0, 1, 2]]]]]}
        assert MultiSolid.from_dict(raw).to_dict() == raw


# ---------------------------------------------------------------------------
# GEOMPRIMITIVE_TYPES dispatch table
# ---------------------------------------------------------------------------

class TestGeomPrimitiveTypes:
    def test_all_seven_keys(self):
        expected = {
            "MultiPoint", "MultiLineString", "MultiSurface", "CompositeSurface",
            "Solid", "CompositeSolid", "MultiSolid",
        }
        assert set(GEOMPRIMITIVE_TYPES.keys()) == expected

    def test_types_are_correct_classes(self):
        assert GEOMPRIMITIVE_TYPES["MultiSurface"] is MultiSurface
        assert GEOMPRIMITIVE_TYPES["Solid"] is Solid
        assert GEOMPRIMITIVE_TYPES["CompositeSolid"] is CompositeSolid


# ---------------------------------------------------------------------------
# geom_primitive_from_dict factory
# ---------------------------------------------------------------------------

class TestGeomPrimitiveFromDict:
    @pytest.mark.parametrize("type_str,cls", [
        ("MultiPoint", MultiPoint),
        ("MultiLineString", MultiLineString),
        ("MultiSurface", MultiSurface),
        ("CompositeSurface", CompositeSurface),
        ("Solid", Solid),
        ("CompositeSolid", CompositeSolid),
        ("MultiSolid", MultiSolid),
    ])
    def test_dispatch(self, type_str, cls):
        raw = {"type": type_str, "lod": "1", "boundaries": []}
        obj = geom_primitive_from_dict(raw)
        assert isinstance(obj, cls)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown geometry type"):
            geom_primitive_from_dict({"type": "WeirdThing", "lod": "1", "boundaries": []})
