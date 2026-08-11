from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .city_objects import ExtensionObject, _AbstractCityObject, city_object_from_dict
from .geomprimitives import GeometryPrimitive, geom_primitive_from_dict


@dataclass
class Transform:
    """Scale and translate factors to convert integer coordinates back to real-world coordinates."""

    scale: list[float]  # exactly 3 numbers: [sx, sy, sz]
    translate: list[float]  # exactly 3 numbers: [tx, ty, tz]

    @classmethod
    def from_dict(cls, data: dict) -> Transform:
        return cls(scale=data["scale"], translate=data["translate"])

    def to_dict(self) -> dict:
        return {"scale": self.scale, "translate": self.translate}


@dataclass
class Metadata:
    """Metadata regarding the spatial dataset (spec §5).

    The six named fields match ISO 19115.  Any other properties land in `extra`.
    `referenceSystem` follows the OGC Name Type Specification URI pattern,
    e.g. "https://www.opengis.net/def/crs/EPSG/0/7415".
    """

    geographical_extent: list[float] | None = (
        None  # [minx, miny, minz, maxx, maxy, maxz]
    )
    identifier: str | None = None
    point_of_contact: dict[str, Any] | None = None  # free-form per spec
    reference_date: str | None = None  # ISO 8601 full-date, e.g. "1977-02-28"
    reference_system: str | None = None  # OGC CRS URI
    title: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)  # non-standard / future fields

    @classmethod
    def from_dict(cls, data: dict) -> Metadata:
        known = {
            "geographicalExtent",
            "identifier",
            "pointOfContact",
            "referenceDate",
            "referenceSystem",
            "title",
        }
        return cls(
            geographical_extent=data.get("geographicalExtent"),
            identifier=data.get("identifier"),
            point_of_contact=data.get("pointOfContact"),
            reference_date=data.get("referenceDate"),
            reference_system=data.get("referenceSystem"),
            title=data.get("title"),
            extra={k: v for k, v in data.items() if k not in known},
        )

    def to_dict(self) -> dict:
        d: dict[str, Any] = {}
        if self.geographical_extent is not None:
            d["geographicalExtent"] = self.geographical_extent
        if self.identifier is not None:
            d["identifier"] = self.identifier
        if self.point_of_contact is not None:
            d["pointOfContact"] = self.point_of_contact
        if self.reference_date is not None:
            d["referenceDate"] = self.reference_date
        if self.reference_system is not None:
            d["referenceSystem"] = self.reference_system
        if self.title is not None:
            d["title"] = self.title
        d.update(self.extra)
        return d


@dataclass
class Appearance:
    """Materials and textures applied to the geometries.

    JSON key mapping (CityJSON uses hyphens, Python uses underscores):
        "vertices-texture"       -> vertices_texture
        "default-theme-texture"  -> default_theme_texture
        "default-theme-material" -> default_theme_material
    """

    materials: list[dict[str, Any]] = field(default_factory=list)
    textures: list[dict[str, Any]] = field(default_factory=list)
    vertices_texture: list[list[float]] = field(default_factory=list)
    default_theme_texture: str | None = None
    default_theme_material: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Appearance:
        return cls(
            materials=data.get("materials", []),
            textures=data.get("textures", []),
            vertices_texture=data.get("vertices-texture", []),
            default_theme_texture=data.get("default-theme-texture"),
            default_theme_material=data.get("default-theme-material"),
        )

    def to_dict(self) -> dict:
        d: dict[str, Any] = {}
        if self.materials:
            d["materials"] = self.materials
        if self.textures:
            d["textures"] = self.textures
        if self.vertices_texture:
            d["vertices-texture"] = self.vertices_texture
        if self.default_theme_texture is not None:
            d["default-theme-texture"] = self.default_theme_texture
        if self.default_theme_material is not None:
            d["default-theme-material"] = self.default_theme_material
        return d


@dataclass
class GeometryTemplates:
    """Reusable geometry templates.

    JSON key mapping:
        "vertices-templates" -> vertices_templates
    """

    templates: list[GeometryPrimitive] = field(default_factory=list)
    vertices_templates: list[list[float]] = field(
        default_factory=list
    )  # JSON: "vertices-templates"

    @classmethod
    def from_dict(cls, data: dict) -> GeometryTemplates:
        templates = [geom_primitive_from_dict(t) for t in data.get("templates", [])]
        return cls(
            templates=templates,
            vertices_templates=data.get("vertices-templates", []),
        )

    def to_dict(self) -> dict:
        d: dict[str, Any] = {}
        if self.templates:
            d["templates"] = [t.to_dict() for t in self.templates]
        if self.vertices_templates:
            d["vertices-templates"] = self.vertices_templates
        return d


@dataclass
class CityJSONDocument:
    """The root object of a CityJSON 2.0 dataset.

    JSON key mapping:
        "geometry-templates" -> geometry_templates
    """

    type: Literal["CityJSON"] = "CityJSON"
    version: Literal["2.0"] = "2.0"
    transform: Transform | None = None

    # Maps unique object IDs to their respective CityObject dataclass
    city_objects: dict[str, _AbstractCityObject | ExtensionObject] = field(
        default_factory=dict
    )

    # Flat list of quantized 3D integer coordinates: [[x1, y1, z1], ...]
    vertices: list[list[int | float]] = field(default_factory=list)

    metadata: Metadata | None = None
    appearance: Appearance | None = None
    extensions: dict[str, dict[str, Any]] = field(default_factory=dict)
    geometry_templates: GeometryTemplates | None = None  # JSON: "geometry-templates"

    @classmethod
    def from_dict(cls, data: dict) -> CityJSONDocument:
        doc = cls(
            type=data.get("type", "CityJSON"),
            version=data.get("version", "2.0"),
            vertices=data.get("vertices", []),
            extensions=data.get("extensions", {}),
        )
        if "transform" in data:
            doc.transform = Transform.from_dict(data["transform"])
        if "metadata" in data:
            doc.metadata = Metadata.from_dict(data["metadata"])
        if "appearance" in data:
            doc.appearance = Appearance.from_dict(data["appearance"])
        if "geometry-templates" in data:
            doc.geometry_templates = GeometryTemplates.from_dict(
                data["geometry-templates"]
            )
        doc.city_objects = {
            k: city_object_from_dict(v) for k, v in data.get("CityObjects", {}).items()
        }
        return doc

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "type": self.type,
            "version": self.version,
            "CityObjects": {k: v.to_dict() for k, v in self.city_objects.items()},
            "vertices": self.vertices,
        }
        if self.transform is not None:
            d["transform"] = self.transform.to_dict()
        if self.metadata is not None:
            d["metadata"] = self.metadata.to_dict()
        if self.appearance is not None:
            d["appearance"] = self.appearance.to_dict()
        if self.geometry_templates is not None:
            d["geometry-templates"] = self.geometry_templates.to_dict()
        if self.extensions:
            d["extensions"] = self.extensions
        return d


# Short alias for the complete CityJSON document model.
CityJSON = CityJSONDocument
