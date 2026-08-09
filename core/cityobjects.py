"""
Python dataclasses for CityJSON 2.0.2 CityObjects.

Generated from:
    https://3d.bk.tudelft.nl/schemas/cityjson/2.0.2/cityobjects.schema.json
    https://3d.bk.tudelft.nl/schemas/cityjson/2.0.2/geomprimitives.schema.json
    https://3d.bk.tudelft.nl/schemas/cityjson/2.0.2/geomtemplates.schema.json

Notes on fidelity to the JSON Schema
-------------------------------------
- `geometry` items are typed using the real dataclasses from
  `geomprimitives.py` (MultiPoint, MultiLineString, MultiSurface,
  CompositeSurface, Solid, CompositeSolid, MultiSolid) and `geomtemplates.py`
  (GeometryInstance). Each CityObject's `geometry` field is a
  `List[Union[...]]` restricted to exactly the types its schema `oneOf`
  allows -- e.g. `Building.geometry` only accepts MultiSurface /
  CompositeSurface / Solid / CompositeSolid, not MultiPoint or
  GeometryInstance, while `BuildingInstallation.geometry` accepts all seven
  primitives plus GeometryInstance.
- Python's type system can't enforce a JSON Schema `oneOf` at runtime --
  these Unions are for static type-checking / documentation, not
  validation.
- `type` is modeled as `Literal[...]` to mirror the schema's `const`.
- Fields required in the schema (e.g. `parents` for *Part/*Installation/
  *ConstructiveElement/*Furniture/*Room/*Storey/*Unit/*HollowSpace types,
  and `children` for CityObjectGroup) default to empty containers here for
  convenience -- enforce their presence yourself if you need strictness.
- `attributes` is left as `Dict[str, Any]` since the schema only says
  `{"type": "object"}` with no further constraints.
- Plain dataclasses (no runtime JSON-Schema validation), zero dependencies
  beyond the standard library and the sibling `geomprimitives` module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union

from geomprimitives import (
    CompositeSolid,
    CompositeSurface,
    MultiLineString,
    MultiPoint,
    MultiSolid,
    MultiSurface,
    Solid,
)
from geomtemplates import GeometryInstance

# ---------------------------------------------------------------------------
# Per-CityObject geometry unions, mirroring each type's `oneOf` list in
# cityobjects.schema.json exactly.
# ---------------------------------------------------------------------------

# Building, BuildingPart, BuildingRoom, BuildingUnit, BuildingStorey,
# Tunnel, TunnelPart, TunnelHollowSpace, Bridge, BridgePart, BridgeRoom
GeomSurfaceOrSolid = Union[MultiSurface, CompositeSurface, Solid, CompositeSolid]

# BuildingInstallation, BuildingConstructiveElement, BuildingFurniture,
# TunnelInstallation, TunnelConstructiveElement, TunnelFurniture,
# BridgeInstallation, BridgeConstructiveElement, BridgeFurniture,
# SolitaryVegetationObject, CityFurniture, OtherConstruction
GeomAnyPrimitiveOrInstance = Union[
    MultiPoint,
    MultiLineString,
    MultiSurface,
    CompositeSurface,
    Solid,
    CompositeSolid,
    MultiSolid,
    GeometryInstance,
]

# Road, Railway, TransportSquare, Waterway
GeomTransportation = Union[MultiLineString, MultiSurface, CompositeSurface]

# WaterBody
GeomWaterBody = Union[MultiLineString, MultiSurface, CompositeSurface, Solid, CompositeSolid]

# PlantCover
GeomPlantCover = Union[MultiSurface, CompositeSurface, Solid, CompositeSolid, MultiSolid]

# LandUse
GeomLandUse = Union[MultiSurface, CompositeSurface]

# CityObjectGroup (no GeometryInstance)
GeomCityObjectGroup = Union[
    MultiPoint, MultiLineString, MultiSurface, CompositeSurface, Solid, CompositeSolid, MultiSolid
]

# GenericCityObject
GeomGeneric = Union[
    MultiPoint,
    MultiLineString,
    Solid,
    MultiSolid,
    CompositeSolid,
    MultiSurface,
    CompositeSurface,
    GeometryInstance,
]


@dataclass
class Address:
    """Item of the `address` array (Building, BuildingUnit, Bridge, BridgePart)."""

    location: Optional[MultiPoint] = None


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


@dataclass
class _AbstractCityObject:
    """Common properties shared by every CityObject (schema: _AbstractCityObject)."""

    attributes: Dict[str, Any] = field(default_factory=dict)
    parents: List[str] = field(default_factory=list)          # IDs of the parents
    children: List[str] = field(default_factory=list)         # IDs of children
    geographicalExtent: Optional[List[float]] = None          # exactly 6 numbers if set


@dataclass
class ExtensionObject:
    """Schema: ExtensionObject. `type` must match pattern (+)([A-Z])\\w+."""

    type: str  # e.g. "+GenericCityObject"


# ---------------------------------------------------------------------------
# Building family
# ---------------------------------------------------------------------------


@dataclass
class _AbstractBuilding(_AbstractCityObject):
    """Shared by Building / BuildingPart."""

    address: List[Address] = field(default_factory=list)
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class Building(_AbstractBuilding):
    type: Literal["Building"] = "Building"


@dataclass
class BuildingPart(_AbstractBuilding):
    type: Literal["BuildingPart"] = "BuildingPart"
    # parents required by schema


@dataclass
class BuildingInstallation(_AbstractCityObject):
    type: Literal["BuildingInstallation"] = "BuildingInstallation"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


@dataclass
class BuildingConstructiveElement(_AbstractCityObject):
    type: Literal["BuildingConstructiveElement"] = "BuildingConstructiveElement"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


@dataclass
class BuildingFurniture(_AbstractCityObject):
    type: Literal["BuildingFurniture"] = "BuildingFurniture"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


@dataclass
class BuildingRoom(_AbstractCityObject):
    type: Literal["BuildingRoom"] = "BuildingRoom"
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)
    # parents required by schema


@dataclass
class BuildingUnit(_AbstractCityObject):
    type: Literal["BuildingUnit"] = "BuildingUnit"
    address: List[Address] = field(default_factory=list)
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)
    # parents required by schema


@dataclass
class BuildingStorey(_AbstractCityObject):
    type: Literal["BuildingStorey"] = "BuildingStorey"
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)
    # parents required by schema


# ---------------------------------------------------------------------------
# Tunnel family
# ---------------------------------------------------------------------------


@dataclass
class Tunnel(_AbstractCityObject):
    type: Literal["Tunnel"] = "Tunnel"
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class TunnelPart(_AbstractCityObject):
    type: Literal["TunnelPart"] = "TunnelPart"
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)
    # parents required by schema


@dataclass
class TunnelInstallation(_AbstractCityObject):
    type: Literal["TunnelInstallation"] = "TunnelInstallation"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


@dataclass
class TunnelConstructiveElement(_AbstractCityObject):
    type: Literal["TunnelConstructiveElement"] = "TunnelConstructiveElement"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


@dataclass
class TunnelHollowSpace(_AbstractCityObject):
    type: Literal["TunnelHollowSpace"] = "TunnelHollowSpace"
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)
    # parents required by schema


@dataclass
class TunnelFurniture(_AbstractCityObject):
    type: Literal["TunnelFurniture"] = "TunnelFurniture"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


# ---------------------------------------------------------------------------
# Bridge family
# ---------------------------------------------------------------------------


@dataclass
class Bridge(_AbstractCityObject):
    type: Literal["Bridge"] = "Bridge"
    address: List[Address] = field(default_factory=list)
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)


@dataclass
class BridgePart(_AbstractCityObject):
    type: Literal["BridgePart"] = "BridgePart"
    address: List[Address] = field(default_factory=list)
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)
    # parents required by schema


@dataclass
class BridgeInstallation(_AbstractCityObject):
    type: Literal["BridgeInstallation"] = "BridgeInstallation"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


@dataclass
class BridgeConstructiveElement(_AbstractCityObject):
    type: Literal["BridgeConstructiveElement"] = "BridgeConstructiveElement"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


@dataclass
class BridgeRoom(_AbstractCityObject):
    type: Literal["BridgeRoom"] = "BridgeRoom"
    geometry: List[GeomSurfaceOrSolid] = field(default_factory=list)
    # parents required by schema


@dataclass
class BridgeFurniture(_AbstractCityObject):
    type: Literal["BridgeFurniture"] = "BridgeFurniture"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)
    # parents required by schema


# ---------------------------------------------------------------------------
# Transportation family
# ---------------------------------------------------------------------------


@dataclass
class _AbstractTransportationComplex(_AbstractCityObject):
    geometry: List[GeomTransportation] = field(default_factory=list)


@dataclass
class Road(_AbstractTransportationComplex):
    type: Literal["Road"] = "Road"


@dataclass
class Railway(_AbstractTransportationComplex):
    type: Literal["Railway"] = "Railway"


@dataclass
class TransportSquare(_AbstractTransportationComplex):
    type: Literal["TransportSquare"] = "TransportSquare"


@dataclass
class Waterway(_AbstractTransportationComplex):
    type: Literal["Waterway"] = "Waterway"


# ---------------------------------------------------------------------------
# Terrain / land / vegetation / water / furniture / other / generic
# ---------------------------------------------------------------------------


@dataclass
class TINRelief(_AbstractCityObject):
    type: Literal["TINRelief"] = "TINRelief"
    geometry: List[CompositeSurface] = field(default_factory=list)  # CompositeSurface only


@dataclass
class WaterBody(_AbstractCityObject):
    type: Literal["WaterBody"] = "WaterBody"
    geometry: List[GeomWaterBody] = field(default_factory=list)


@dataclass
class PlantCover(_AbstractCityObject):
    type: Literal["PlantCover"] = "PlantCover"
    geometry: List[GeomPlantCover] = field(default_factory=list)


@dataclass
class SolitaryVegetationObject(_AbstractCityObject):
    type: Literal["SolitaryVegetationObject"] = "SolitaryVegetationObject"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class LandUse(_AbstractCityObject):
    type: Literal["LandUse"] = "LandUse"
    geometry: List[GeomLandUse] = field(default_factory=list)


@dataclass
class CityFurniture(_AbstractCityObject):
    type: Literal["CityFurniture"] = "CityFurniture"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class OtherConstruction(_AbstractCityObject):
    type: Literal["OtherConstruction"] = "OtherConstruction"
    geometry: List[GeomAnyPrimitiveOrInstance] = field(default_factory=list)


@dataclass
class CityObjectGroup(_AbstractCityObject):
    type: Literal["CityObjectGroup"] = "CityObjectGroup"
    children_roles: List[Optional[str]] = field(default_factory=list)
    geometry: List[GeomCityObjectGroup] = field(default_factory=list)
    # children required by schema


@dataclass
class GenericCityObject(_AbstractCityObject):
    type: Literal["GenericCityObject"] = "GenericCityObject"
    geometry: List[GeomGeneric] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Convenience: union of every concrete CityObject type + type-string lookup
# ---------------------------------------------------------------------------

CityObject = Union[
    Building,
    BuildingPart,
    BuildingInstallation,
    BuildingConstructiveElement,
    BuildingFurniture,
    BuildingRoom,
    BuildingUnit,
    BuildingStorey,
    Tunnel,
    TunnelPart,
    TunnelInstallation,
    TunnelConstructiveElement,
    TunnelHollowSpace,
    TunnelFurniture,
    Bridge,
    BridgePart,
    BridgeInstallation,
    BridgeConstructiveElement,
    BridgeRoom,
    BridgeFurniture,
    Road,
    Railway,
    TransportSquare,
    Waterway,
    TINRelief,
    WaterBody,
    PlantCover,
    SolitaryVegetationObject,
    LandUse,
    CityFurniture,
    OtherConstruction,
    CityObjectGroup,
    GenericCityObject,
]

CITYOBJECT_TYPES: Dict[str, type] = {
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
    "TunnelHollowSpace": TunnelHollowSpace,
    "TunnelFurniture": TunnelFurniture,
    "Bridge": Bridge,
    "BridgePart": BridgePart,
    "BridgeInstallation": BridgeInstallation,
    "BridgeConstructiveElement": BridgeConstructiveElement,
    "BridgeRoom": BridgeRoom,
    "BridgeFurniture": BridgeFurniture,
    "Road": Road,
    "Railway": Railway,
    "TransportSquare": TransportSquare,
    "Waterway": Waterway,
    "TINRelief": TINRelief,
    "WaterBody": WaterBody,
    "PlantCover": PlantCover,
    "SolitaryVegetationObject": SolitaryVegetationObject,
    "LandUse": LandUse,
    "CityFurniture": CityFurniture,
    "OtherConstruction": OtherConstruction,
    "CityObjectGroup": CityObjectGroup,
    "GenericCityObject": GenericCityObject,
}
