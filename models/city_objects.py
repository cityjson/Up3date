"""
Python dataclasses for CityJSON 2.0.2 city objects.

Spec: https://www.cityjson.org/specs/2.0.2/
Schema: https://3d.bk.tudelft.nl/schemas/cityjson/2.0.2/cityjson.min.schema.json
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Literal

from .geomprimitives import (
    CompositeSolid,
    CompositeSurface,
    GeometryPrimitive,
    MultiLineString,
    MultiPoint,
    MultiSolid,
    MultiSurface,
    Solid,
    geom_primitive_from_dict,
)
from .geomtemplates import GeometryInstance

# ---------------------------------------------------------------------------
# PEP 695 Type Aliases (Python 3.12+)
# ---------------------------------------------------------------------------

type GeomSurfaceOrSolid = MultiSurface | CompositeSurface | Solid | CompositeSolid

type GeomAnyPrimitiveOrInstance = (
    MultiPoint
    | MultiLineString
    | MultiSurface
    | CompositeSurface
    | Solid
    | CompositeSolid
    | MultiSolid
    | GeometryInstance
)

type GeomTransportation = MultiLineString | MultiSurface | CompositeSurface

type GeomWaterBody = (
    MultiLineString | MultiSurface | CompositeSurface | Solid | CompositeSolid
)

type GeomPlantCover = (
    MultiSurface | CompositeSurface | Solid | CompositeSolid | MultiSolid
)

type GeomLandUse = MultiSurface | CompositeSurface

type GeomCityObjectGroup = (
    MultiPoint
    | MultiLineString
    | MultiSurface
    | CompositeSurface
    | Solid
    | CompositeSolid
    | MultiSolid
)

type GeomGeneric = (
    MultiPoint
    | MultiLineString
    | MultiSurface
    | CompositeSurface
    | Solid
    | CompositeSolid
    | MultiSolid
    | GeometryInstance
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _geom_any_from_dict(data: dict) -> GeometryPrimitive | GeometryInstance:
    """Deserialize any geometry object, including GeometryInstance."""
    if data.get("type") == "GeometryInstance":
        return GeometryInstance.from_dict(data)
    return geom_primitive_from_dict(data)


@dataclass
class Address:
    """Item of the `address` array (Building, BuildingUnit, Bridge, BridgePart).

    The spec says address members "are not prescribed"; only `location` has a
    defined structure.  All other fields are kept verbatim in `extra`.
    """

    location: MultiPoint | None = None
    extra: dict[str, Any] = field(default_factory=dict)  # unprescribed fields

    @classmethod
    def from_dict(cls, data: dict) -> Address:
        location = None
        if "location" in data:
            location = MultiPoint.from_dict(data["location"])
        extra = {k: v for k, v in data.items() if k != "location"}
        return cls(location=location, extra=extra)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {}
        if self.location is not None:
            d["location"] = self.location.to_dict()
        d.update(self.extra)
        return d


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


@dataclass
class _AbstractCityObject:
    """Common properties shared by every CityObject (schema: _AbstractCityObject)."""

    attributes: dict[str, Any] = field(default_factory=dict)
    parents: list[str] = field(default_factory=list)  # IDs of the parents
    children: list[str] = field(default_factory=list)  # IDs of children
    geographical_extent: list[float] | None = None  # exactly 6 numbers if set

    @classmethod
    def from_dict(cls, data: dict) -> _AbstractCityObject:
        valid = {f.name for f in dataclasses.fields(cls)}
        kwargs: dict[str, Any] = {
            "attributes": data.get("attributes", {}),
            "parents": data.get("parents", []),
            "children": data.get("children", []),
            "geographical_extent": data.get("geographicalExtent"),
        }
        if "geometry" in valid:
            kwargs["geometry"] = [
                _geom_any_from_dict(g) for g in data.get("geometry", [])
            ]
        if "address" in valid:
            kwargs["address"] = [Address.from_dict(a) for a in data.get("address", [])]
        if "children_roles" in valid:
            kwargs["children_roles"] = data.get("children_roles", [])
        return cls(**{k: v for k, v in kwargs.items() if k in valid})

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"type": self.type}  # type: ignore[attr-defined]
        if self.attributes:
            d["attributes"] = self.attributes
        if self.parents:
            d["parents"] = self.parents
        if self.children:
            d["children"] = self.children
        if self.geographical_extent is not None:
            d["geographicalExtent"] = self.geographical_extent
        if hasattr(self, "geometry"):
            d["geometry"] = [g.to_dict() for g in self.geometry]
        if hasattr(self, "address") and self.address:
            d["address"] = [a.to_dict() for a in self.address]
        if hasattr(self, "children_roles") and self.children_roles:
            d["children_roles"] = self.children_roles
        return d


@dataclass
class ExtensionObject:
    """Schema: ExtensionObject. `type` must match pattern (+)([A-Z])\\w+."""

    type: str  # e.g. "+GenericCityObject"

    @classmethod
    def from_dict(cls, data: dict) -> ExtensionObject:
        return cls(type=data["type"])

    def to_dict(self) -> dict:
        return {"type": self.type}


# ---------------------------------------------------------------------------
# Building family
# ---------------------------------------------------------------------------


@dataclass
class _AbstractBuilding(_AbstractCityObject):
    """Shared by Building / BuildingPart."""

    address: list[Address] = field(default_factory=list)
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class Building(_AbstractBuilding):
    type: Literal["Building"] = "Building"


@dataclass
class BuildingPart(_AbstractBuilding):
    type: Literal["BuildingPart"] = "BuildingPart"


@dataclass
class BuildingInstallation(_AbstractCityObject):
    type: Literal["BuildingInstallation"] = "BuildingInstallation"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class BuildingConstructiveElement(_AbstractCityObject):
    type: Literal["BuildingConstructiveElement"] = "BuildingConstructiveElement"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class BuildingFurniture(_AbstractCityObject):
    type: Literal["BuildingFurniture"] = "BuildingFurniture"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class BuildingRoom(_AbstractCityObject):
    type: Literal["BuildingRoom"] = "BuildingRoom"
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class BuildingUnit(_AbstractCityObject):
    type: Literal["BuildingUnit"] = "BuildingUnit"
    address: list[Address] = field(default_factory=list)
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class BuildingStorey(_AbstractCityObject):
    type: Literal["BuildingStorey"] = "BuildingStorey"
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tunnel family
# ---------------------------------------------------------------------------


@dataclass
class Tunnel(_AbstractCityObject):
    type: Literal["Tunnel"] = "Tunnel"
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class TunnelPart(_AbstractCityObject):
    type: Literal["TunnelPart"] = "TunnelPart"
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class TunnelInstallation(_AbstractCityObject):
    type: Literal["TunnelInstallation"] = "TunnelInstallation"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class TunnelConstructiveElement(_AbstractCityObject):
    type: Literal["TunnelConstructiveElement"] = "TunnelConstructiveElement"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class TunnelFurniture(_AbstractCityObject):
    type: Literal["TunnelFurniture"] = "TunnelFurniture"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class TunnelHollowSpace(_AbstractCityObject):
    type: Literal["TunnelHollowSpace"] = "TunnelHollowSpace"
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Bridge family
# ---------------------------------------------------------------------------


@dataclass
class Bridge(_AbstractCityObject):
    type: Literal["Bridge"] = "Bridge"
    address: list[Address] = field(default_factory=list)
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class BridgePart(_AbstractCityObject):
    type: Literal["BridgePart"] = "BridgePart"
    address: list[Address] = field(default_factory=list)
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class BridgeInstallation(_AbstractCityObject):
    type: Literal["BridgeInstallation"] = "BridgeInstallation"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class BridgeConstructiveElement(_AbstractCityObject):
    type: Literal["BridgeConstructiveElement"] = "BridgeConstructiveElement"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class BridgeFurniture(_AbstractCityObject):
    type: Literal["BridgeFurniture"] = "BridgeFurniture"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class BridgeRoom(_AbstractCityObject):
    type: Literal["BridgeRoom"] = "BridgeRoom"
    geometry: list[GeomSurfaceOrSolid] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Transportation family
# ---------------------------------------------------------------------------


@dataclass
class Road(_AbstractCityObject):
    type: Literal["Road"] = "Road"
    geometry: list[GeomTransportation] = field(default_factory=list)


@dataclass
class Railway(_AbstractCityObject):
    type: Literal["Railway"] = "Railway"
    geometry: list[GeomTransportation] = field(default_factory=list)


@dataclass
class TransportSquare(_AbstractCityObject):
    type: Literal["TransportSquare"] = "TransportSquare"
    geometry: list[GeomTransportation] = field(default_factory=list)


@dataclass
class Waterway(_AbstractCityObject):
    type: Literal["Waterway"] = "Waterway"
    geometry: list[GeomTransportation] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Vegetation family
# ---------------------------------------------------------------------------


@dataclass
class SolitaryVegetationObject(_AbstractCityObject):
    type: Literal["SolitaryVegetationObject"] = "SolitaryVegetationObject"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class PlantCover(_AbstractCityObject):
    type: Literal["PlantCover"] = "PlantCover"
    geometry: list[GeomPlantCover] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Environment, LandUse, and Water family
# ---------------------------------------------------------------------------


@dataclass
class WaterBody(_AbstractCityObject):
    type: Literal["WaterBody"] = "WaterBody"
    geometry: list[GeomWaterBody] = field(default_factory=list)


@dataclass
class TINRelief(_AbstractCityObject):
    type: Literal["TINRelief"] = "TINRelief"
    geometry: list[CompositeSurface] = field(default_factory=list)


@dataclass
class LandUse(_AbstractCityObject):
    type: Literal["LandUse"] = "LandUse"
    geometry: list[GeomLandUse] = field(default_factory=list)


@dataclass
class CityFurniture(_AbstractCityObject):
    type: Literal["CityFurniture"] = "CityFurniture"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Generic and Group types
# ---------------------------------------------------------------------------


@dataclass
class OtherConstruction(_AbstractCityObject):
    type: Literal["OtherConstruction"] = "OtherConstruction"
    geometry: list[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class GenericCityObject(_AbstractCityObject):
    type: Literal["GenericCityObject"] = "GenericCityObject"
    geometry: list[GeomGeneric] = field(default_factory=list)


@dataclass
class CityObjectGroup(_AbstractCityObject):
    """A group of City Objects.

    Per spec §2.5, group members are stored in the inherited `children` field
    (JSON key "children").  `children_roles` is an optional parallel array
    describing each member's role in the group.
    """

    type: Literal["CityObjectGroup"] = "CityObjectGroup"
    children_roles: list[str | None] = field(default_factory=list)
    geometry: list[GeomCityObjectGroup] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Dispatch table and factory function
# ---------------------------------------------------------------------------

CITY_OBJECT_TYPES: dict[str, Any] = {
    "Building": Building,
    "BuildingPart": BuildingPart,
    "BuildingInstallation": BuildingInstallation,
    "BuildingConstructiveElement": BuildingConstructiveElement,
    "BuildingFurniture": BuildingFurniture,
    "BuildingRoom": BuildingRoom,
    "BuildingUnit": BuildingUnit,
    "BuildingStorey": BuildingStorey,
    "Tunnel": Tunnel,
    "TunnelPart": TunnelPart,
    "TunnelInstallation": TunnelInstallation,
    "TunnelConstructiveElement": TunnelConstructiveElement,
    "TunnelFurniture": TunnelFurniture,
    "TunnelHollowSpace": TunnelHollowSpace,
    "Bridge": Bridge,
    "BridgePart": BridgePart,
    "BridgeInstallation": BridgeInstallation,
    "BridgeConstructiveElement": BridgeConstructiveElement,
    "BridgeFurniture": BridgeFurniture,
    "BridgeRoom": BridgeRoom,
    "Road": Road,
    "Railway": Railway,
    "TransportSquare": TransportSquare,
    "Waterway": Waterway,
    "SolitaryVegetationObject": SolitaryVegetationObject,
    "PlantCover": PlantCover,
    "WaterBody": WaterBody,
    "TINRelief": TINRelief,
    "LandUse": LandUse,
    "CityFurniture": CityFurniture,
    "OtherConstruction": OtherConstruction,
    "GenericCityObject": GenericCityObject,
    "CityObjectGroup": CityObjectGroup,
}


def city_object_from_dict(data: dict) -> _AbstractCityObject | ExtensionObject:
    """Deserialize a CityObject dict using `type` for dispatch.

    Extension objects (type starting with '+') are returned as ExtensionObject.
    Unknown types raise ValueError.
    """
    type_str = data.get("type", "")
    if type_str.startswith("+"):
        return ExtensionObject.from_dict(data)
    city_object_class = CITY_OBJECT_TYPES.get(type_str)
    if city_object_class is None:
        raise ValueError(f"Unknown CityObject type: {type_str!r}")
    return city_object_class.from_dict(data)
