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


# Nested int-or-null arrays used for semantics.values / material.values /
# texture.values -- depth varies by primitive, so kept generic.
NestedIntOrNull = Any


@dataclass
class GeometrySemantics:
    """schema: `semantics` object shared by all seven primitives."""

    surfaces: list[Semantics] = field(default_factory=list)
    values: NestedIntOrNull = None  # required by schema, may be null


@dataclass
class MaterialValue:
    """schema: value of each key in the `material` object.

    Exactly one of `value` / `values` should be set (schema `oneOf`).
    """

    value: int | None = None
    values: NestedIntOrNull = None


# schema: "material" -- object keyed by theme name -> MaterialValue
Material = dict[str, MaterialValue]


@dataclass
class TextureTheme:
    """schema: value of each key in the `texture` object."""

    values: NestedIntOrNull = None


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
# Primitives
# ---------------------------------------------------------------------------


@dataclass
class MultiPoint:
    lod: Lod
    boundaries: MultiPointBoundaries = field(default_factory=list)
    type: Literal["MultiPoint"] = "MultiPoint"
    semantics: GeometrySemantics | None = None
    # no material / texture (additionalProperties: false in schema)


@dataclass
class MultiLineString:
    lod: Lod
    boundaries: MultiLineStringBoundaries = field(default_factory=list)
    type: Literal["MultiLineString"] = "MultiLineString"
    semantics: GeometrySemantics | None = None
    # no material / texture (additionalProperties: false in schema)


@dataclass
class MultiSurface:
    lod: Lod
    boundaries: SurfaceBoundaries = field(default_factory=list)
    type: Literal["MultiSurface"] = "MultiSurface"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None


@dataclass
class CompositeSurface:
    lod: Lod
    boundaries: SurfaceBoundaries = field(default_factory=list)
    type: Literal["CompositeSurface"] = "CompositeSurface"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None


@dataclass
class Solid:
    lod: Lod
    boundaries: SolidBoundaries = field(default_factory=list)
    type: Literal["Solid"] = "Solid"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None


@dataclass
class CompositeSolid:
    lod: Lod
    boundaries: MultiSolidBoundaries = field(default_factory=list)
    type: Literal["CompositeSolid"] = "CompositeSolid"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None


@dataclass
class MultiSolid:
    lod: Lod
    boundaries: MultiSolidBoundaries = field(default_factory=list)
    type: Literal["MultiSolid"] = "MultiSolid"
    semantics: GeometrySemantics | None = None
    material: Material | None = None
    texture: Texture | None = None


# Union of every primitive defined in geomprimitives.schema.json.
# (GeometryInstance from geomtemplates.schema.json is intentionally not
# included here -- see cityobjects.py.)
GeometryPrimitive = (
    MultiPoint
    | MultiLineString
    | MultiSurface
    | CompositeSurface
    | Solid
    | CompositeSolid
    | MultiSolid
)

GEOMPRIMITIVE_TYPES: dict[str, type] = {
    "MultiPoint": MultiPoint,
    "MultiLineString": MultiLineString,
    "MultiSurface": MultiSurface,
    "CompositeSurface": CompositeSurface,
    "Solid": Solid,
    "CompositeSolid": CompositeSolid,
    "MultiSolid": MultiSolid,
}
