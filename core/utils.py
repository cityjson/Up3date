"""Blender CityJSON plugin utils module

This modules provides utility methods for the importing/exporting
processing of CityJSON files
"""

from collections.abc import Sequence
from typing import Any, Protocol, cast

import bpy

from ..models.cityjson import CityJSONDocument, Metadata, Transform
from ..models.geomprimitives import Semantics
from .blender_types import (
    BlenderCollection,
    BlenderMaterial,
    BlenderObject,
    BlenderPolygon,
    CustomPropertyOwner,
    Vector,
)


class GeometryOwner(Protocol):
    geometry: list[Any]


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
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)


def clean_list(values: list[Any]) -> list[Any]:
    """Creates a list of non list in case lists nested in lists exist"""

    while isinstance(values[0], list):
        values = values[0]

    return values


def assign_properties[PropertyOwner: CustomPropertyOwner](
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


def coord_translate_axis_origin(
    vertices: Sequence[Sequence[float]],
) -> tuple[tuple[tuple[float, float, float], ...], float, float, float]:
    """Translates the vertices to the origin (0, 0, 0)"""
    # Finding minimum value of x,y,z
    minx = min(i[0] for i in vertices)
    miny = min(i[1] for i in vertices)
    minz = min(i[2] for i in vertices)

    return coord_translate_by_offset(vertices, minx, miny, minz)


def coord_translate_by_offset(
    vertices: Sequence[Sequence[float]], offx: float, offy: float, offz: float
) -> tuple[tuple[tuple[float, float, float], ...], float, float, float]:
    """Translates the vertices by minx, miny and minz"""
    # Calculating new coordinates
    translated_x = [i[0] - offx for i in vertices]
    translated_y = [i[1] - offy for i in vertices]
    translated_z = [i[2] - offz for i in vertices]

    return (tuple(zip(translated_x, translated_y, translated_z)), offx, offy, offz)


def original_coordinates(
    vertices: Sequence[Sequence[float]], minx: float, miny: float, minz: float
) -> tuple[tuple[float, float, float], ...]:
    """Translates the vertices from origin to original"""
    # Calculating original coordinates
    original_x = [i[0] + minx for i in vertices]
    original_y = [i[1] + miny for i in vertices]
    original_z = [i[2] + minz for i in vertices]

    return tuple(zip(original_x, original_y, original_z))


def clean_buffer(
    vertices: Sequence[Any], bounds: Sequence[Sequence[int]]
) -> tuple[list[Any], list[tuple[int, ...]]]:
    """Cleans the vertex index buffer from unused vertices"""

    new_bounds = []
    new_vertices = []
    i = 0
    for bound in bounds:
        new_bound = []

        for vertex_id in bound:
            new_vertices.append(vertices[vertex_id])
            new_bound.append(i)
            i = i + 1

        new_bounds.append(tuple(new_bound))

    return new_vertices, new_bounds


def get_geometry_name(objid: str, geom: Any, index: int) -> str:
    """Returns the name of the provided geometry"""
    if geom.type == "GeometryInstance":
        return f"{index}: [GeometryInstance] {objid}"
    return f"{index}: [LoD{geom.lod}] {objid}"


def create_empty_object(name: str) -> BlenderObject:
    """Returns an empty blender object"""

    new_object = bpy.data.objects.new(name, None)

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
        mesh_data = bpy.data.meshes.new(name)

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
            mesh_data.polygons.foreach_set("material_index", material_indices)
        elif len(material_indices) > len(faces):
            print(
                f"Object {name} has {len(faces)} faces but {len(material_indices)} semantic surfaces!"
            )

        mesh_data.update()

    new_object = bpy.data.objects.new(name, mesh_data)

    return new_object


def get_collection(collection_name: str) -> BlenderCollection:
    """Returns a collection with the given name"""

    if collection_name in bpy.data.collections:
        return bpy.data.collections[collection_name]

    new_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(new_collection)

    return new_collection


########## Exporter functions ##########


def store_semantic_surfaces(
    doc: CityJSONDocument,
    city_object: BlenderObject,
    index: int,
    city_object_id: str,
) -> dict[str, int] | None:
    """Populates geometry semantics from Blender materials and returns a name→index lookup."""
    if not city_object.data.materials:
        return None

    city_object_model = cast(GeometryOwner, doc.city_objects[city_object_id])
    geom = city_object_model.geometry[index]
    semantic_surface_lookup: dict[str, int] = {}
    semantic_surface_index = 0
    for material in city_object.data.materials:
        if material is None:
            continue
        semantic_type = material["type"]
        if not isinstance(semantic_type, str):
            continue
        geom.semantics.surfaces.append(Semantics(type=semantic_type))
        semantic_surface_lookup[material.name] = semantic_surface_index
        semantic_surface_index += 1

    return semantic_surface_lookup


def link_face_semantic_surface(
    doc: CityJSONDocument,
    city_object: BlenderObject,
    index: int,
    city_object_id: str,
    semantic_surface_lookup: dict[str, int] | None,
    face: BlenderPolygon,
) -> None:
    """Links a mesh face to its corresponding semantic surface index."""
    if not city_object.data.materials:
        return
    city_object_model = cast(GeometryOwner, doc.city_objects[city_object_id])
    geom = city_object_model.geometry[index]
    material = city_object.data.materials[face.material_index]
    if material is None:
        geom.semantics.values[0].append(None)
        return

    name = material.name
    assert semantic_surface_lookup is not None
    geom.semantics.values[0].append(semantic_surface_lookup[name])


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


def write_vertices_to_cityjson(
    city_object: BlenderObject, vertex: Vector, doc: CityJSONDocument
) -> None:
    """Writes a vertex to doc.vertices after translating to the original CRS position."""
    coord = city_object.matrix_world @ vertex
    if (
        "transformed" in bpy.context.scene.world
        and "Axis_Origin_X_translation" in bpy.context.scene.world
    ):
        # Translate back to original CRS coordinates, then reverse the quantisation transform
        x, y, z = (
            coord[0] - bpy.context.scene.world["Axis_Origin_X_translation"],
            coord[1] - bpy.context.scene.world["Axis_Origin_Y_translation"],
            coord[2] - bpy.context.scene.world["Axis_Origin_Z_translation"],
        )
        x = round(
            (x - bpy.context.scene.world["transform.X_translate"])
            / bpy.context.scene.world["transform.X_scale"]
        )
        y = round(
            (y - bpy.context.scene.world["transform.Y_translate"])
            / bpy.context.scene.world["transform.Y_scale"]
        )
        z = round(
            (z - bpy.context.scene.world["transform.Z_translate"])
            / bpy.context.scene.world["transform.Z_scale"]
        )
        doc.vertices.append([x, y, z])
    elif "Axis_Origin_X_translation" in bpy.context.scene.world:
        doc.vertices.append(
            [
                coord[0] - bpy.context.scene.world["Axis_Origin_X_translation"],
                coord[1] - bpy.context.scene.world["Axis_Origin_Y_translation"],
                coord[2] - bpy.context.scene.world["Axis_Origin_Z_translation"],
            ]
        )
    else:
        doc.vertices.append([coord[0], coord[1], coord[2]])


def remove_vertex_duplicates(doc: CityJSONDocument, precision: int = 3) -> int:
    """Finds all duplicate vertices within a given precision and merges them.
    Adapted from https://github.com/cityjson/cjio/blob/faf422afe94b4787aeffa9b2e53ee71b32546320/cjio/cityjson.py#L1208
    """
    if doc.transform is not None:
        precision = 0

    def update_geom_indices(a: list[Any], newids: list[int]) -> None:
        for i, each in enumerate(a):
            if isinstance(each, list):
                update_geom_indices(each, newids)
            else:
                a[i] = newids[each]

    totalinput = len(doc.vertices)
    h: dict[str, int] = {}
    newids = [-1] * len(doc.vertices)
    newvertices: list[str] = []
    for i, input_vertex in enumerate(doc.vertices):
        s = f"{{x:.{precision}f}} {{y:.{precision}f}} {{z:.{precision}f}}".format(
            x=input_vertex[0], y=input_vertex[1], z=input_vertex[2]
        )
        if s not in h:
            newid = len(h)
            newids[i] = newid
            h[s] = newid
            newvertices.append(s)
        else:
            newids[i] = h[s]

    for co_value in doc.city_objects.values():
        co: Any = co_value
        if hasattr(co, "geometry"):
            for geom in co.geometry:
                update_geom_indices(geom.boundaries, newids)

    newv2: Any = []
    for encoded_vertex in newvertices:
        if doc.transform is not None:
            parsed_vertex: Any = list(map(int, encoded_vertex.split()))
        else:
            parsed_vertex = list(map(float, encoded_vertex.split()))
        newv2.append(parsed_vertex)
    doc.vertices = newv2
    return totalinput - len(doc.vertices)


def export_transformation_parameters(doc: CityJSONDocument) -> None:
    """Reads the transform stored in scene world properties and sets doc.transform."""
    if "transformed" in bpy.context.scene.world:
        print("Exporting transformation parameters...")
        doc.transform = Transform(
            scale=[
                bpy.context.scene.world["transform.X_scale"],
                bpy.context.scene.world["transform.Y_scale"],
                bpy.context.scene.world["transform.Z_scale"],
            ],
            translate=[
                bpy.context.scene.world["transform.X_translate"],
                bpy.context.scene.world["transform.Y_translate"],
                bpy.context.scene.world["transform.Z_translate"],
            ],
        )


def export_metadata(doc: CityJSONDocument) -> None:
    """Computes and sets doc.metadata from scene world properties and object bounds."""
    print("Exporting metadata...")
    ref_sys = bpy.context.scene.world.get("CRS")
    minim, maxim = bbox(bpy.data.objects)
    extent = list(minim) + [round(c, 3) for c in maxim]
    doc.metadata = Metadata(
        reference_system=ref_sys if ref_sys else None,
        geographical_extent=extent,
    )


def export_parent_child(doc: CityJSONDocument) -> None:
    """Stores parent/child relationships in doc.city_objects from Blender."""
    print("\nSaving parents-children relations...")
    for city_object in bpy.data.objects:
        if city_object.parent and city_object.type == "EMPTY":
            parent_id = city_object.parent.name
            child_id = city_object.name
            parent_co = doc.city_objects.get(parent_id)
            child_co = doc.city_objects.get(child_id)
            if (
                parent_co is not None
                and hasattr(parent_co, "children")
                and child_id not in parent_co.children
            ):
                parent_co.children.append(child_id)
            if (
                child_co is not None
                and hasattr(child_co, "parents")
                and parent_id not in child_co.parents
            ):
                child_co.parents.append(parent_id)
