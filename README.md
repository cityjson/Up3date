# Up3date

Up3date is a Blender add-on for importing, inspecting, editing, and exporting
[CityJSON 2.0](https://www.cityjson.org/specs/2.0.2/) 3D city models. City
object attributes, relationships, levels of detail (LoDs), coordinates, and
semantic surfaces are represented in Blender through object and material
custom properties.

The add-on was originally developed by Konstantinos Mastorakis ([konmast3r](https://github.com/konmast3r/))
as part of the MSc Geomatics programme at TU Delft and was further developed
for the MSc thesis [An integrative workflow for 3D city model versioning](http://resolver.tudelft.nl/uuid:a7f7f0c8-7a34-454e-973a-d55f5b8b0dfe).

## Requirements

- Blender 5.0 or newer

The add-on follows the CityJSON schemas and document structure described in
the linked specification.

## CityJSON support

The importer and exporter support the CityJSON document structure, including:

- City Objects, attributes, parent/child relationships, and extension City
  Objects whose type starts with `+`;
- `MultiPoint`, `MultiLineString`, `MultiSurface`, `CompositeSurface`, `Solid`,
  `CompositeSolid`, and `MultiSolid` geometry primitives;
- LoDs from `0` through `3`, including decimal LoDs such as `2.2`;
- semantic surfaces and their custom properties;
- coordinate `transform` objects and `metadata`, including the CRS;
- `appearance`, `geometry-templates`, `GeometryInstance`, and `extensions`.

There is an important distinction between parsing and Blender visualization:
`MultiSurface`, `CompositeSurface`, and `Solid` geometries are converted to
editable Blender meshes. Other CityJSON geometry types, including
`MultiPoint`, `MultiLineString`, `CompositeSolid`, `MultiSolid`, and
`GeometryInstance`, are kept as empty Blender objects with their serialized
geometry attached so they can be written back during export. Their geometry is
not currently expanded into editable Blender meshes.

Appearance, geometry templates, and extensions are preserved when exporting an
imported scene, but textures and CityJSON material definitions are not applied
as Blender materials. Semantic surfaces are represented using Blender
materials instead.

## Testing datasets

Sample datasets are available from the official
[CityJSON datasets](https://www.cityjson.org/datasets/). CityGML datasets can
be converted with the official [CityJSON conversion tools](https://www.cityjson.org/help/users/conversion/).
Large datasets may take several minutes to import, depending on the machine.

## Installation

1. Download this repository as a ZIP, or create a ZIP containing the add-on
   files.
2. In Blender, open `Edit > Preferences > Add-ons` and choose `Install...`.
3. Select the ZIP and install it.
4. Enable **Up3date** in the add-on list.

When updating an installed copy, disable and re-enable the add-on after
installing the new ZIP.

## Usage

### Importing a CityJSON file

Choose `File > Import > CityJSON (.json)`, select a file, and confirm the
import. The file selector provides these options:

- **Materials' type — Surfaces**: create materials from semantic surface
  types such as `RoofSurface` and `WallSurface`.
- **Materials' type — City Objects**: create materials from City Object types
  such as `Building` and `Road`.
- **Reuse materials**: reuse semantic-surface materials with the same type.
  This can improve import speed, but per-surface custom properties cannot be
  represented independently when materials are shared.
- **Clean scene**: remove existing Blender objects, collections, and stored
  CityJSON scene properties before importing.

The importer applies a CityJSON `transform` to recover real-world
coordinates, then translates the model near the scene origin for Blender.
The CRS and the translation parameters are stored under `World Properties` so
the exporter can reconstruct the original coordinate space. A collection named
`LoD<lod>` is created for each imported mesh LoD.

For large files, Blender's console reports import progress and timing. If the
model is not visible, select a mesh object in the Outliner and use `View >
Frame Selected` (or press `Home`). Keep the viewport in `Object Mode` while
starting an import or export.

![Accessing the attributes of objects](images/attributes.png)
![Accessing the semantics of LoD2 (or higher) geometries](images/semantics.png)
![The translation parameters with the CRS information](images/world_properties.png)

City Object attributes are available under an object's `Object Properties >
Custom Properties`. Semantic surface properties are available on the material
assigned to a mesh face.

### Exporting a CityJSON file

Choose `File > Export > CityJSON (.json)`. The exporter creates a CityJSON
document from the current Blender scene. It recognizes imported Up3date
objects automatically. For geometry created manually, use the following
structure:

1. Create an **Empty** for each City Object. Name it with the CityJSON object
   ID and add a custom property `type` such as `Building`, `Road`, or
   `GenericCityObject`. Add CityJSON attributes with the prefix
   `attributes.`; for example, `attributes.measuredHeight`. Nested attributes
   use dots, such as `attributes.address.postalCode`.
2. Create one **Mesh** child per geometry. Add string custom properties
   `type` and `lod`. `type` must be `MultiSurface`, `CompositeSurface`, or
   `Solid` for geometry edited as a Blender mesh. For example, use `lod: 2`
   and `type: MultiSurface`.
3. To export semantic surfaces, assign materials to mesh faces and add a
   string custom property `type` to each material, for example
   `type: WallSurface` or `type: RoofSurface`.
4. Export the scene.

The exporter can remove duplicate vertices. Its **Remove vertex duplicates**
option is enabled by default; **Precision** controls the decimal precision
used when comparing untransformed vertices. Imported CityJSON transforms are
preserved and used when coordinates are written back.

![Adding a new Mesh object with its necessary custom properties](images/new_object_mesh.png)
![Adding the parent Empty object with optional custom properties](images/new_object_empty.png)
![Adding semantic information to a geometry surface](images/semantic_property.png)

## Development

For development, testing, and contribution instructions see
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
