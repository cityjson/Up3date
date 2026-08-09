"""Tests for models/cityobjects.py — CityJSON 2.0.2 CityObject types."""

import pytest

from models.cityobjects import (
    CITYOBJECT_TYPES,
    Address,
    Bridge,
    BridgeConstructiveElement,
    BridgeFurniture,
    BridgeInstallation,
    BridgePart,
    BridgeRoom,
    Building,
    BuildingConstructiveElement,
    BuildingFurniture,
    BuildingInstallation,
    BuildingPart,
    BuildingRoom,
    BuildingStorey,
    BuildingUnit,
    CityFurniture,
    CityObjectGroup,
    ExtensionObject,
    GenericCityObject,
    LandUse,
    OtherConstruction,
    PlantCover,
    Railway,
    Road,
    SolitaryVegetationObject,
    TINRelief,
    TransportSquare,
    Tunnel,
    TunnelConstructiveElement,
    TunnelFurniture,
    TunnelHollowSpace,
    TunnelInstallation,
    TunnelPart,
    WaterBody,
    Waterway,
    cityobject_from_dict,
)
from models.geomprimitives import MultiSurface, Solid


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------

class TestAddress:
    def test_empty(self):
        a = Address()
        assert a.location is None
        assert a.to_dict() == {}

    def test_from_dict_no_location(self):
        a = Address.from_dict({})
        assert a.location is None

    def test_from_dict_with_location(self):
        raw = {
            "location": {"type": "MultiPoint", "lod": "0", "boundaries": [0]},
        }
        a = Address.from_dict(raw)
        assert a.location is not None
        assert a.location.type == "MultiPoint"

    def test_to_dict_with_location(self):
        raw = {"location": {"type": "MultiPoint", "lod": "0", "boundaries": [0]}}
        d = Address.from_dict(raw).to_dict()
        assert "location" in d
        assert d["location"]["type"] == "MultiPoint"


# ---------------------------------------------------------------------------
# _AbstractCityObject — base fields
# ---------------------------------------------------------------------------

class TestAbstractCityObjectBaseFields:
    def test_defaults(self):
        b = Building()
        assert b.attributes == {}
        assert b.parents == []
        assert b.children == []
        assert b.geographicalExtent is None

    def test_from_dict_base_fields(self):
        raw = {
            "type": "Building",
            "attributes": {"height": 10.0},
            "parents": ["p1"],
            "children": ["c1", "c2"],
            "geographicalExtent": [0.0, 0.0, 0.0, 1.0, 1.0, 10.0],
            "geometry": [],
        }
        b = Building.from_dict(raw)
        assert b.attributes == {"height": 10.0}
        assert b.parents == ["p1"]
        assert b.children == ["c1", "c2"]
        assert b.geographicalExtent == [0.0, 0.0, 0.0, 1.0, 1.0, 10.0]

    def test_to_dict_omits_empty_base_fields(self):
        b = Building()
        d = b.to_dict()
        assert "attributes" not in d
        assert "parents" not in d
        assert "children" not in d
        assert "geographicalExtent" not in d


# ---------------------------------------------------------------------------
# Building family
# ---------------------------------------------------------------------------

class TestBuilding:
    def test_type_literal(self):
        assert Building().type == "Building"

    def test_from_dict_with_geometry(self):
        raw = {
            "type": "Building",
            "geometry": [
                {"type": "MultiSurface", "lod": "1", "boundaries": [[[[0, 1, 2]]]]}
            ],
        }
        b = Building.from_dict(raw)
        assert len(b.geometry) == 1
        assert isinstance(b.geometry[0], MultiSurface)

    def test_from_dict_with_address(self):
        raw = {
            "type": "Building",
            "address": [{}],
            "geometry": [],
        }
        b = Building.from_dict(raw)
        assert len(b.address) == 1

    def test_to_dict_includes_type(self):
        d = Building().to_dict()
        assert d["type"] == "Building"

    def test_roundtrip(self):
        raw = {
            "type": "Building",
            "attributes": {"measuredHeight": 12.5},
            "children": ["bp-1"],
            "geometry": [
                {"type": "MultiSurface", "lod": "2", "boundaries": [[[[0, 1, 2, 3]]]]}
            ],
        }
        result = Building.from_dict(raw).to_dict()
        assert result["type"] == "Building"
        assert result["attributes"] == {"measuredHeight": 12.5}
        assert result["children"] == ["bp-1"]
        assert result["geometry"][0]["type"] == "MultiSurface"


class TestBuildingPart:
    def test_type_literal(self):
        assert BuildingPart().type == "BuildingPart"


class TestBuildingInstallation:
    def test_type_literal(self):
        assert BuildingInstallation().type == "BuildingInstallation"


class TestBuildingConstructiveElement:
    def test_type_literal(self):
        assert BuildingConstructiveElement().type == "BuildingConstructiveElement"


class TestBuildingFurniture:
    def test_type_literal(self):
        assert BuildingFurniture().type == "BuildingFurniture"


class TestBuildingRoom:
    def test_type_literal(self):
        assert BuildingRoom().type == "BuildingRoom"


class TestBuildingUnit:
    def test_type_literal(self):
        assert BuildingUnit().type == "BuildingUnit"

    def test_has_address_field(self):
        bu = BuildingUnit()
        assert hasattr(bu, "address")


class TestBuildingStorey:
    def test_type_literal(self):
        assert BuildingStorey().type == "BuildingStorey"


# ---------------------------------------------------------------------------
# Tunnel family
# ---------------------------------------------------------------------------

class TestTunnel:
    def test_type_literal(self):
        assert Tunnel().type == "Tunnel"

    def test_from_dict_with_solid(self):
        raw = {
            "type": "Tunnel",
            "geometry": [{"type": "Solid", "lod": "2", "boundaries": [[[[0, 1, 2]]]]}],
        }
        t = Tunnel.from_dict(raw)
        assert isinstance(t.geometry[0], Solid)


class TestTunnelPart:
    def test_type_literal(self):
        assert TunnelPart().type == "TunnelPart"


class TestTunnelInstallation:
    def test_type_literal(self):
        assert TunnelInstallation().type == "TunnelInstallation"


class TestTunnelConstructiveElement:
    def test_type_literal(self):
        assert TunnelConstructiveElement().type == "TunnelConstructiveElement"


class TestTunnelFurniture:
    def test_type_literal(self):
        assert TunnelFurniture().type == "TunnelFurniture"


class TestTunnelHollowSpace:
    def test_type_literal(self):
        assert TunnelHollowSpace().type == "TunnelHollowSpace"


# ---------------------------------------------------------------------------
# Bridge family
# ---------------------------------------------------------------------------

class TestBridge:
    def test_type_literal(self):
        assert Bridge().type == "Bridge"

    def test_has_address_field(self):
        assert hasattr(Bridge(), "address")


class TestBridgePart:
    def test_type_literal(self):
        assert BridgePart().type == "BridgePart"

    def test_has_address_field(self):
        assert hasattr(BridgePart(), "address")


class TestBridgeInstallation:
    def test_type_literal(self):
        assert BridgeInstallation().type == "BridgeInstallation"


class TestBridgeConstructiveElement:
    def test_type_literal(self):
        assert BridgeConstructiveElement().type == "BridgeConstructiveElement"


class TestBridgeFurniture:
    def test_type_literal(self):
        assert BridgeFurniture().type == "BridgeFurniture"


class TestBridgeRoom:
    def test_type_literal(self):
        assert BridgeRoom().type == "BridgeRoom"


# ---------------------------------------------------------------------------
# Transportation
# ---------------------------------------------------------------------------

class TestTransportation:
    @pytest.mark.parametrize("cls,type_str", [
        (Road, "Road"),
        (Railway, "Railway"),
        (TransportSquare, "TransportSquare"),
        (Waterway, "Waterway"),
    ])
    def test_type_literals(self, cls, type_str):
        assert cls().type == type_str


# ---------------------------------------------------------------------------
# Vegetation
# ---------------------------------------------------------------------------

class TestVegetation:
    def test_solitary_vegetation_object(self):
        assert SolitaryVegetationObject().type == "SolitaryVegetationObject"

    def test_plant_cover(self):
        assert PlantCover().type == "PlantCover"


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class TestEnvironment:
    def test_water_body(self):
        assert WaterBody().type == "WaterBody"

    def test_land_use(self):
        assert LandUse().type == "LandUse"

    def test_city_furniture(self):
        assert CityFurniture().type == "CityFurniture"

    def test_tin_relief(self):
        assert TINRelief().type == "TINRelief"

    def test_tin_relief_geometry_is_composite_surface(self):
        from models.geomprimitives import CompositeSurface
        raw = {
            "type": "TINRelief",
            "geometry": [{"type": "CompositeSurface", "lod": "1", "boundaries": [[[0, 1, 2]]]}],
        }
        obj = TINRelief.from_dict(raw)
        assert isinstance(obj.geometry[0], CompositeSurface)


# ---------------------------------------------------------------------------
# Generic types
# ---------------------------------------------------------------------------

class TestGenericTypes:
    def test_other_construction(self):
        assert OtherConstruction().type == "OtherConstruction"

    def test_generic_city_object(self):
        assert GenericCityObject().type == "GenericCityObject"


# ---------------------------------------------------------------------------
# CityObjectGroup
# ---------------------------------------------------------------------------

class TestCityObjectGroup:
    def test_type_literal(self):
        assert CityObjectGroup().type == "CityObjectGroup"

    def test_group_members_are_in_children(self):
        # Spec §2.5: group members are stored in "children", not "members"
        cog = CityObjectGroup()
        assert hasattr(cog, "children")
        assert cog.children == []

    def test_from_dict_members_via_children(self):
        raw = {
            "type": "CityObjectGroup",
            "children": ["building-1", "building-2"],
            "geometry": [],
        }
        cog = CityObjectGroup.from_dict(raw)
        assert cog.children == ["building-1", "building-2"]

    def test_children_roles(self):
        raw = {
            "type": "CityObjectGroup",
            "children": ["b1", "b3"],
            "children_roles": ["residential building", "voting location"],
            "geometry": [],
        }
        cog = CityObjectGroup.from_dict(raw)
        assert cog.children_roles == ["residential building", "voting location"]

    def test_to_dict_includes_children_roles(self):
        cog = CityObjectGroup(children=["a", "b"], children_roles=["r1", "r2"])
        d = cog.to_dict()
        assert d["children"] == ["a", "b"]
        assert d["children_roles"] == ["r1", "r2"]

    def test_to_dict_omits_empty_children_roles(self):
        cog = CityObjectGroup()
        d = cog.to_dict()
        assert "children_roles" not in d


# ---------------------------------------------------------------------------
# ExtensionObject
# ---------------------------------------------------------------------------

class TestExtensionObject:
    def test_from_dict(self):
        eo = ExtensionObject.from_dict({"type": "+MyExtension"})
        assert eo.type == "+MyExtension"

    def test_to_dict(self):
        assert ExtensionObject(type="+Thing").to_dict() == {"type": "+Thing"}


# ---------------------------------------------------------------------------
# CITYOBJECT_TYPES dispatch table
# ---------------------------------------------------------------------------

class TestCityObjectTypes:
    def test_covers_all_standard_types(self):
        expected = {
            "Building", "BuildingPart", "BuildingInstallation", "BuildingConstructiveElement",
            "BuildingFurniture", "BuildingRoom", "BuildingUnit", "BuildingStorey",
            "Tunnel", "TunnelPart", "TunnelInstallation", "TunnelConstructiveElement",
            "TunnelFurniture", "TunnelHollowSpace",
            "Bridge", "BridgePart", "BridgeInstallation", "BridgeConstructiveElement",
            "BridgeFurniture", "BridgeRoom",
            "Road", "Railway", "TransportSquare", "Waterway",
            "SolitaryVegetationObject", "PlantCover",
            "WaterBody", "TINRelief", "LandUse", "CityFurniture", "OtherConstruction",
            "GenericCityObject", "CityObjectGroup",
        }
        assert set(CITYOBJECT_TYPES.keys()) == expected


# ---------------------------------------------------------------------------
# cityobject_from_dict factory
# ---------------------------------------------------------------------------

class TestCityObjectFromDict:
    def test_building(self):
        obj = cityobject_from_dict({"type": "Building", "geometry": []})
        assert isinstance(obj, Building)

    def test_road(self):
        obj = cityobject_from_dict({"type": "Road", "geometry": []})
        assert isinstance(obj, Road)

    def test_extension_object(self):
        obj = cityobject_from_dict({"type": "+MySuperObject"})
        assert isinstance(obj, ExtensionObject)
        assert obj.type == "+MySuperObject"

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown CityObject type"):
            cityobject_from_dict({"type": "Banana"})

    @pytest.mark.parametrize("type_str", list(CITYOBJECT_TYPES.keys()))
    def test_all_types_dispatch(self, type_str):
        obj = cityobject_from_dict({"type": type_str, "geometry": []})
        assert obj.type == type_str
