"""
Python dataclasses for CityJSON 2.0.2 geometric primitives.

Generated from:
    https://3d.bk.tudelft.nl/schemas/cityjson/2.0.2/geomprimitives.schema.json

Boundary nesting per primitive (schema `boundaries` arrays):
    MultiPoint       : [ index, ... ]                                        (1 level)
    MultiLineString  : [ [ index, ... ], ... ]                               (2 levels)
    MultiSurface /
    CompositeSurface : [ [ [ index, ... ], ... ], ... ]                      (3 levels: surface -> rings -> indices)
    Solid            : [ [ [ [ index, ... ], ... ], ... ], ... ]             (4 levels: shell -> surfaces -> rings -> indices)
    CompositeSolid /
    MultiSolid       : [ [ [ [ [ index, ... ], ... ], ... ], ... ], ... ]    (5 levels: solid -> shell -> surfaces -> rings -> indices)

`semantics.values` mirrors the boundaries nesting one level shallower (it
indexes into `semantics.surfaces` at the ring/surface level), and `material`
/`texture` values follow similarly documented but schema-permissive shapes.
Those are kept as loosely-typed nested structures (`Any`) since the schema
itself doesn't constrain them beyond "nested arrays of int-or-null".

Only MultiSurface, CompositeSurface, Solid, CompositeSolid and MultiSolid
support `material`/`texture`; MultiPoint and MultiLineString support only
`semantics` (per `additionalProperties: false` in the schema).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------

# schema: "Lods" enum
Lod = Literal[
    "0",
    "1",
    "2",
    "3",
    "0.0",
    "0.1",
    "0.2",
    "0.3",
    "1.0",
    "1.1",
    "1.2",
    "1.3",
    "2.0",
    "2.1",
    "2.2",
    "2.3",
    "3.0",
    "3.1",
    "3.2",
    "3.3",
]


@dataclass
class Semantics:
    """schema: Semantics. Only `type` is formally constrained; any other
    keys (e.g. `parent`, `children`, custom attributes) are permitted by
    the schema (no `additionalProperties: false`) and are captured in
    `extra`.
    """

    type: str
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> Semantics:
        type_ = data["type"]
        extra = {k: v for k, v in data.items() if k != "type"}
        return cls(type=type_, extra=extra)

    def to_dict(self) -> dict:
        return {"type": self.type, **self.extra}


# Nested int-or-null arrays used for semantics.values / material.values /
# texture.values -- depth varies by primitive, so kept generic.
NestedIntOrNull = Any


@dataclass
class GeometrySemantics:
    """schema: `semantics` object shared by all seven primitives."""

    surfaces: list[Semantics] = field(default_factory=list)
    values: NestedIntOrNull = None  # required by schema, may be null

    @classmethod
    def from_dict(cls, data: dict) -> GeometrySemantics:
        return cls(
            surfaces=[Semantics.from_dict(s) for s in data.get("surfaces", [])],
            values=data.get("values"),
        )

    def to_dict(self) -> dict:
        return {
            "surfaces": [s.to_dict() for s in self.surfaces],
            "values": self.values,
        }


@dataclass
class MaterialValue:
    """schema: value of each key in the `material` object.

    Exactly one of `value` / `values` should be set (schema `oneOf`).
    """

    value: int | None = None
    values: NestedIntOrNull = None

    @classmethod
    def from_dict(cls, data: dict) -> MaterialValue:
        return cls(value=data.get("value"), values=data.get("values"))

    def to_dict(self) -> dict:
        if self.value is not None:
            return {"value": self.value}
        return {"values": self.values}


# schema: "material" -- object keyed by theme name -> MaterialValue
Material = dict[str, MaterialValue]


@dataclass
class TextureTheme:
    """schema: value of each key in the `texture` object."""

    values: NestedIntOrNull = None

    @classmethod
    def from_dict(cls, data: dict) -> TextureTheme:
        return cls(values=data.get("values"))

    def to_dict(self) -> dict:
        return {"values": self.values}


# schema: "texture" -- object keyed by theme name -> TextureTheme
Texture = dict[str, TextureTheme]


# ---------------------------------------------------------------------------
# Boundary type aliases (exact nesting per primitive)
# ---------------------------------------------------------------------------

MultiPointBoundaries = list[int]
MultiLineStringBoundaries = list[list[int]]
SurfaceBoundaries = list[list[list[int]]]  # MultiSurface / CompositeSurface
SolidBoundaries = list[list[list[list[int]]]]  # Solid
MultiSolidBoundaries = list[list[list[list[list[int]]]]]  # CompositeSolid / MultiSolid


# ---------------------------------------------------------------------------
# Shared serialization helpers
# ---------------------------------------------------------------------------


def _geom_from_dict(cls: type[Any], data: dict, *, has_appearance: bool) -> Any:
    """Shared from_dict logic for all geometry primitives."""
    obj = cls(lod=data["lod"], boundaries=data.get("boundaries", []))
    if "semantics" in data:
        obj.semantics = GeometrySemantics.from_dict(data["semantics"])
    if has_appearance:
        if "material" in data:
            obj.material = {
                k: MaterialValue.from_dict(v) for k, v in data["material"].items()
            }
        if "texture" in data:
            obj.texture = {
                k: TextureTheme.from_dict(v) for k, v in data["texture"].items()
            }
    return obj


def _geom_to_dict(obj: Any) -> dict:
    """Shared to_dict logic for all geometry primitives."""
    d: dict[str, Any] = {
        "type": obj.type,
        "lod": obj.lod,
        "boundaries": obj.boundaries,
    }
    if obj.semantics is not None:
        d["semantics"] = obj.semantics.to_dict()
    if hasattr(obj, "material") and obj.material is not None:
        d["material"] = {k: v.to_dict() for k, v in obj.material.items()}
    if hasattr(obj, "texture") and obj.texture is not None:
        d["texture"] = {k: v.to_dict() for k, v in obj.texture.items()}
    return d


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


@dataclass
class MultiPoint:
    lod: Lod
    boundaries: MultiPointBoundaries = field(default_factory=list)
    type: Literal["MultiPoint"] = "MultiPoint"
    semantics: GeometrySemantics | None = None
    # no material / texture (additionalProperties: false in schema)

    @classmethod
    def from_dict(cls, data: dict) -> MultiPoint:
        return _geom_from_dict(cls, data, has_appearance=False)

    def to_dict(self) -> dict:
        return _geom_to_dict(self)


@dataclass
class MultiLineString:
    lod: Lod
    boundaries: MultiLineStringBoundaries = field(default_factory=list)
    type: Literal["MultiLineString"] = "MultiLineString"
    semantics: GeometrySemantics | None = None
    # no material / texture (additionalProperties: false in schema)

    @classmethod
    def from_dict(cls, data: dict) -> MultiLineString:
        return _geom_from_dict(cls, data, has_appearance=False)

    def to_dict(self) -> dict:
        return _geom_to_dict(self)


@dataclass
class MultiSurface:
    lod: Lod
    boundaries: SurfaceBoundaries = field(default_factory=list)
    type: Literal["MultiSurface"] = "MultiSurface"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None

    @classmethod
    def from_dict(cls, data: dict) -> MultiSurface:
        return _geom_from_dict(cls, data, has_appearance=True)

    def to_dict(self) -> dict:
        return _geom_to_dict(self)


@dataclass
class CompositeSurface:
    lod: Lod
    boundaries: SurfaceBoundaries = field(default_factory=list)
    type: Literal["CompositeSurface"] = "CompositeSurface"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CompositeSurface:
        return _geom_from_dict(cls, data, has_appearance=True)

    def to_dict(self) -> dict:
        return _geom_to_dict(self)


@dataclass
class Solid:
    lod: Lod
    boundaries: SolidBoundaries = field(default_factory=list)
    type: Literal["Solid"] = "Solid"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Solid:
        return _geom_from_dict(cls, data, has_appearance=True)

    def to_dict(self) -> dict:
        return _geom_to_dict(self)


@dataclass
class CompositeSolid:
    lod: Lod
    boundaries: MultiSolidBoundaries = field(default_factory=list)
    type: Literal["CompositeSolid"] = "CompositeSolid"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CompositeSolid:
        return _geom_from_dict(cls, data, has_appearance=True)

    def to_dict(self) -> dict:
        return _geom_to_dict(self)


@dataclass
class MultiSolid:
    lod: Lod
    boundaries: MultiSolidBoundaries = field(default_factory=list)
    type: Literal["MultiSolid"] = "MultiSolid"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None

    @classmethod
    def from_dict(cls, data: dict) -> MultiSolid:
        return _geom_from_dict(cls, data, has_appearance=True)

    def to_dict(self) -> dict:
        return _geom_to_dict(self)


# Union of every primitive defined in geomprimitives.schema.json.
# (GeometryInstance from geomtemplates.schema.json is intentionally not
# included here -- see city_objects.py.)
GeometryPrimitive = (
    MultiPoint
    | MultiLineString
    | MultiSurface
    | CompositeSurface
    | Solid
    | CompositeSolid
    | MultiSolid
)

GEOMETRY_PRIMITIVE_TYPES: dict[str, Any] = {
    "MultiPoint": MultiPoint,
    "MultiLineString": MultiLineString,
    "MultiSurface": MultiSurface,
    "CompositeSurface": CompositeSurface,
    "Solid": Solid,
    "CompositeSolid": CompositeSolid,
    "MultiSolid": MultiSolid,
}


def geom_primitive_from_dict(data: dict) -> GeometryPrimitive:
    """Deserialize a geometry primitive dict using the `type` field for dispatch."""
    type_str = data.get("type", "")
    geometry_class = GEOMETRY_PRIMITIVE_TYPES.get(type_str)
    if geometry_class is None:
        raise ValueError(f"Unknown geometry type: {type_str!r}")
    return geometry_class.from_dict(data)
