"""
Python dataclasses for CityJSON 2.0.2 CityObjects.

Generated from:
    https://tudelft.nl
    https://tudelft.nl
    https://tudelft.nl
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

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

type GeomWaterBody = MultiLineString | MultiSurface | CompositeSurface | Solid | CompositeSolid

type GeomPlantCover = MultiSurface | CompositeSurface | Solid | CompositeSolid | MultiSolid

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
    | Solid
    | MultiSolid
    | CompositeSolid
    | MultiSurface
    | CompositeSurface
    | GeometryInstance
)


@dataclass
class Address:
    """Item of the `address` array (Building, BuildingUnit, Bridge, BridgePart)."""

    location: MultiPoint | None = None


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


@dataclass
class _AbstractCityObject:
    """Common properties shared by every CityObject (schema: _AbstractCityObject)."""

    attributes: dict[str, Any] = field(default_factory=dict)
    parents: list[str] = field(default_factory=list)  # IDs of the parents
    children: list[str] = field(default_factory=list)  # IDs of children
    geographicalExtent: list[float] | None = None  # exactly 6 numbers if set


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
    type: Literal["CityObjectGroup"] = "CityObjectGroup"
    geometry: list[GeomCityObjectGroup] = field(default_factory=list)
