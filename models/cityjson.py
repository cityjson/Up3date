from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from models.cityobjects import ExtensionObject, _AbstractCityObject


@dataclass
class Transform:
    """Scale and translate factors to convert integer coordinates back to real-world coordinates."""
    scale: list[float]  # exactly 3 numbers: [x, y, z]
    translate: list[float]  # exactly 3 numbers: [x, y, z]


@dataclass
class Metadata:
    """Metadata regarding the spatial dataset (geographical extent, coordinate reference system, etc.)."""
    geographicalExtent: list[float] | None = None  # exactly 6 numbers: [minx, miny, minz, maxx, maxy, maxz]
    referenceSystem: str | dict[str, Any] | None = None  # CRS identifier or object
    # Add other standard optional fields like datasetTitle, referenceDate if needed
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Appearance:
    """Materials and textures applied to the geometries."""
    materials: list[dict[str, Any]] = field(default_factory=list)
    textures: list[dict[str, Any]] = field(default_factory=list)
    vertices_texture: list[list[float]] = field(default_factory=list)  # Handled as vertices_texture in pure Python


@dataclass
class GeometryTemplates:
    """Reusable geometry templates (templates array and their corresponding vertices)."""
    templates: list[Any] = field(default_factory=list)  # list of Geometry objects used as templates
    vertices: list[list[int]] = field(default_factory=list)


@dataclass
class CityJSONDocument:
    """The root object of a CityJSON 2.0 dataset."""
    type: Literal["CityJSON"] = "CityJSON"
    version: Literal["2.0"] = "2.0"
    transform: Transform | None = None  # technically optional, but practically essential for quantized datasets

    # Maps unique object IDs to their respective CityObject dataclass
    # Using a union of your abstract types or a generic alias
    CityObjects: dict[str, _AbstractCityObject | ExtensionObject] = field(default_factory=dict)

    # Flat list of quantized 3D coordinates: [[x1, y1, z1], [x2, y2, z2], ...]
    vertices: list[list[int]] = field(default_factory=list)

    metadata: Metadata | None = None
    appearance: Appearance | None = None
    extensions: dict[str, dict[str, Any]] = field(default_factory=dict)
    geometry_templates: GeometryTemplates | None = None



# A couple of schema details worth noting

# version should be "2.0" even for the 2.0.2 specification.

# vertices are integer coordinates in the stored file; the transform converts them to real-world floats.

# CityObjects should be dict[str, CityObject], not dict[str, dict[str, Any]]—that's the whole benefit of the generated model.

# This gives you a fully typed root object while staying faithful to the CityJSON 2.0.2 schema.


# One thing I'd change before putting this into Up3date
#
# For the four JSON objects above, I'd use Pythonic field names internally, but explicitly map them to the CityJSON names when serializing:
#
# Python	CityJSON
# vertices_texture	"vertices-texture"
# default_theme_texture	"default-theme-texture"
# default_theme_material	"default-theme-material"
# vertices_templates	"vertices-templates"
#
# This is preferable to having Python attributes such as:
#
# appearance.vertices-texture
#
# which isn't valid Python.
#
# Also, GeometryTemplates.templates should not ultimately be list[object]. It should be:
#
# list[MultiPoint | MultiLineString | MultiSurface |
#      CompositeSurface | Solid | CompositeSolid | MultiSolid]
#
# using the geometry dataclasses you already have. The specification says the templates array contains Geometry Objects.
#
# Similarly, the metadata geographicalExtent should represent exactly six values, and Transform.scale / translate exactly three values. The 2.0.2 spec explicitly requires those shapes.
#
# The appearance model above follows the six core metadata properties and the 2.0.2 Appearance/Material/Texture definitions.
#
# One further issue: pointOfContact.address is intentionally a free-form object in the CityJSON spec, so keeping that as dict[str, object] is appropriate rather than inventing an address schema.
#
# If we're going to make the Up3date model genuinely 2.0.2-correct, I'd next make GeometryTemplates fully typed against the existing geometry dataclasses and then build a proper CityJSON root dataclass around these.
