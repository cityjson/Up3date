"""Blender scene utilities used by the CityJSON importer and exporter."""

from collections.abc import Sequence
from typing import Any, Protocol, TypeVar

import bpy

from .blender_types import (
    BlenderCollection,
    BlenderMaterial,
    BlenderObject,
    CustomPropertyOwner,
)


class GeometryOwner(Protocol):
    geometry: list[Any]


PropertyOwner = TypeVar("PropertyOwner", bound=CustomPropertyOwner)


CITYJSON_ID_PROPERTY = "cityjson_id"
CITYJSON_GEOMETRY_PROPERTY = "cityjson_geometry"
CITYJSON_DOCUMENT_EXTRAS_PROPERTY = "cityjson_document_extras"


def blender_safe_name(name: str) -> str:
    """Avoid numeric dot suffixes that Blender parses as duplicate counters."""
    prefix, separator, suffix = name.rpartition(".")
    if separator and suffix.isdigit():
        return f"{prefix}_{suffix}"
    return name


def get_cityjson_id(city_object: BlenderObject) -> str:
    """Return the preserved CityJSON identifier, falling back to the Blender name."""
    cityjson_id = city_object.get(CITYJSON_ID_PROPERTY)
    return cityjson_id if isinstance(cityjson_id, str) else city_object.name


########## Importer functions ##########


def remove_scene_objects() -> None:
    """Clears the scenes of any objects and removes world's custom properties
    and collections"""
    # Delete world custom properties
    if bpy.context.scene.world.keys():
        for custom_property in list(bpy.context.scene.world.keys()):
            del bpy.context.scene.world[custom_property]
    # Remove all objects without relying on operator context (VIEW_3D not guaranteed)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    # Deleting previously existing collections
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)


def assign_properties(
    obj: PropertyOwner, props: dict[str, Any], prefix: list[str] | None = None
) -> PropertyOwner:
    """Assigns the custom properties to obj based on the props"""

    if prefix is None:
        prefix = []
    for prop, value in props.items():
        if prop in ["geometry", "children", "parents"]:
            continue

        if isinstance(value, dict):
            obj = assign_properties(obj, value, prefix + [prop])

        else:
            full_name = ".".join(prefix + [prop])
            obj[full_name[:63]] = value

    return obj


def create_empty_object(name: str) -> BlenderObject:
    """Returns an empty blender object"""

    new_object = bpy.data.objects.new(blender_safe_name(name), None)

    return new_object


def create_mesh_object(
    name: str,
    vertices: Sequence[Sequence[float]],
    faces: Sequence[Sequence[int]],
    materials: Sequence[BlenderMaterial],
    material_indices: Sequence[int | None],
) -> BlenderObject:
    """Returns a mesh blender object"""

    mesh_data = None

    if faces:
        mesh_data = bpy.data.meshes.new(blender_safe_name(name))

        for material in materials:
            mesh_data.materials.append(material)

        indices = [i for face in faces for i in face]

        mesh_data.vertices.add(len(vertices))
        mesh_data.loops.add(len(indices))
        mesh_data.polygons.add(len(faces))

        coords = [c for v in vertices for c in v]

        loop_totals = [len(face) for face in faces]
        loop_starts = []
        i = 0
        for face in faces:
            loop_starts.append(i)
            i += len(face)

        mesh_data.vertices.foreach_set("co", coords)
        mesh_data.loops.foreach_set("vertex_index", indices)
        mesh_data.polygons.foreach_set("loop_start", loop_starts)
        mesh_data.polygons.foreach_set("loop_total", loop_totals)
        if len(material_indices) == len(faces):
            safe_material_indices = [
                material_index
                if isinstance(material_index, int)
                and 0 <= material_index < len(materials)
                else 0
                for material_index in material_indices
            ]
            mesh_data.polygons.foreach_set("material_index", safe_material_indices)
        elif len(material_indices) > len(faces):
            print(
                f"Object {name} has {len(faces)} faces but {len(material_indices)} semantic surfaces!"
            )

        mesh_data.update()

    new_object = bpy.data.objects.new(blender_safe_name(name), mesh_data)

    return new_object


def get_collection(collection_name: str) -> BlenderCollection:
    """Returns a collection with the given name"""

    if collection_name in bpy.data.collections:
        return bpy.data.collections[collection_name]

    new_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(new_collection)

    return new_collection


########## Exporter functions ##########


def bbox(objects: Sequence[BlenderObject]) -> tuple[list[float], list[float]]:
    """Calculates the bounding box of the objects given"""
    # Initialization
    obj = objects[0]
    bbox = obj.bound_box
    xmax = bbox[0][0]
    ymax = bbox[0][1]
    zmax = bbox[0][2]
    xmin = xmax
    ymin = ymax
    zmin = zmax
    world_max_extent = [xmax, ymax, zmax]
    world_min_extent = [xmin, ymin, zmin]

    # Calculating bbox of the whole scene
    for obj in objects:
        bbox = obj.bound_box

        xmax = bbox[0][0]
        ymax = bbox[0][1]
        zmax = bbox[0][2]

        xmin = xmax
        ymin = ymax
        zmin = zmax

        for i in range(len(bbox)):
            xmax = max(xmax, bbox[i][0])
            xmin = min(xmin, bbox[i][0])

            ymax = max(ymax, bbox[i][1])
            ymin = min(ymin, bbox[i][1])

            zmax = max(zmax, bbox[i][2])
            zmin = min(zmin, bbox[i][2])

        object_max_extent = [xmax, ymax, zmax]
        object_min_extent = [xmin, ymin, zmin]

        world_max_extent[0] = max(world_max_extent[0], object_max_extent[0])
        world_max_extent[1] = max(world_max_extent[1], object_max_extent[1])
        world_max_extent[2] = max(world_max_extent[2], object_max_extent[2])
        world_min_extent[0] = min(world_min_extent[0], object_min_extent[0])
        world_min_extent[1] = min(world_min_extent[1], object_min_extent[1])
        world_min_extent[2] = min(world_min_extent[2], object_min_extent[2])

    # Translating back to original
    if "Axis_Origin_X_translation" in bpy.context.scene.world:
        world_min_extent[0] -= bpy.context.scene.world["Axis_Origin_X_translation"]
        world_min_extent[1] -= bpy.context.scene.world["Axis_Origin_Y_translation"]
        world_min_extent[2] -= bpy.context.scene.world["Axis_Origin_Z_translation"]

        world_max_extent[0] -= bpy.context.scene.world["Axis_Origin_X_translation"]
        world_max_extent[1] -= bpy.context.scene.world["Axis_Origin_Y_translation"]
        world_max_extent[2] -= bpy.context.scene.world["Axis_Origin_Z_translation"]

    return world_min_extent, world_max_extent
