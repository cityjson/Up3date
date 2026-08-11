# Changelog

All notable changes to Up3date are documented here.

## [Unreleased]

## [0.1.0]

### Changed

- Expand support to Blender 5.0 and newer by making Up3date compatible with
  its Python 3.11 runtime and testing Blender 5.0.1, 5.1.2, and 5.2.0 with
  matching Python environments in the headless integration pipeline.
- Publish the installable release asset using its `up3date-<version>.zip`
  filename without an additional display label.

## [0.0.0]

### Added

- Add typed CityJSON 2.0.2 document models with `from_dict` and `to_dict`
  serialization for City Objects, geometry primitives, semantic surfaces,
  transforms, metadata, appearances, geometry templates, and geometry
  instances.
- Support standard City Object types, extension City Objects, attributes,
  geographical extents, members, and parent/child relationships.
- Support `MultiPoint`, `MultiLineString`, `MultiSurface`,
  `CompositeSurface`, `Solid`, `CompositeSolid`, and `MultiSolid` geometry,
  including integer and decimal LoD values.
- Import `MultiSurface`, `CompositeSurface`, and `Solid` geometries as editable
  Blender meshes, with City Object data stored as custom properties and
  semantic surfaces represented as Blender materials.
- Export Blender meshes, City Object attributes, semantic surfaces,
  relationships, metadata, CRS information, transforms, and deduplicated
  vertices as a typed CityJSON document.
- Preserve appearances, extensions, geometry templates, geometry instances,
  unsupported geometry types, and their original CityJSON identifiers during
  Blender import/export round trips.
- Add public model exports for the supported CityJSON document, City Object,
  geometry, and semantics types.

### Changed

- Update the add-on for Blender 5.2 and move Blender-dependent registration to
  `addon.py`, leaving a lightweight package entry point.
- Preserve original coordinate space when importing transformed datasets and
  restore per-object world transformations correctly during export.
- Add structural Blender API types and comprehensive annotations across the
  add-on, core, and model layers.
- Standardize Python identifiers and module names around `city_object` and
  `city_objects`.
- Adopt `uv` as the dependency and environment manager with a reproducible
  `uv.lock` lockfile.
