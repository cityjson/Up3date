"""Module to manipulate objects in Blender regarding CityJSON"""

import json
import sys
import time
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, Protocol, TypeAlias, cast

import bpy
import idprop

from ..models.city_objects import CITY_OBJECT_TYPES, ExtensionObject, GenericCityObject
from ..models.cityjson import CityJSONDocument
from ..models.geomprimitives import (
    GEOMETRY_PRIMITIVE_TYPES,
    GeometryPrimitive,
    GeometrySemantics,
    geom_primitive_from_dict,
)
from ..models.geomtemplates import GeometryInstance
from .blender_types import (
    BlenderObject,
    PolygonCollection,
    VertexCollection,
)
from .cityjson_utils import (
    CITYJSON_DOCUMENT_EXTRAS_PROPERTY,
    CITYJSON_GEOMETRY_PROPERTY,
    CITYJSON_ID_PROPERTY,
    export_metadata,
    export_parent_child,
    export_transformation_parameters,
    link_face_semantic_surface,
    remove_vertex_duplicates,
    store_semantic_surfaces,
    write_vertices_to_cityjson,
)
from .material import (
    BasicMaterialFactory,
    CityObjectTypeMaterialFactory,
    ReuseMaterialFactory,
    TypedCityObject,
)
from .scene import get_cityjson_id


class GeometryContainer(Protocol):
    geometry: list[Any]


class ParsedCityObject(TypedCityObject, Protocol):
    parents: list[str]

    def to_dict(self) -> dict[str, Any]: ...


MaterialFactory = (
    BasicMaterialFactory | ReuseMaterialFactory | CityObjectTypeMaterialFactory
)

GeometryModel: TypeAlias = GeometryPrimitive | GeometryInstance


class CityJSONExporter:
    def __init__(
        self,
        filepath: str,
        check_for_duplicates: bool = True,
        precision: int = 3,
    ) -> None:
        self.filepath = filepath
        self.check_for_duplicates = check_for_duplicates
        self.precision = precision

    @staticmethod
    def initialize_document() -> CityJSONDocument:
        doc = CityJSONDocument()
        stored_extras = bpy.context.scene.world.get(CITYJSON_DOCUMENT_EXTRAS_PROPERTY)
        if not isinstance(stored_extras, str):
            return doc

        extras = json.loads(stored_extras)
        restored = CityJSONDocument.from_dict(
            {
                "type": "CityJSON",
                "version": "2.0",
                "CityObjects": {},
                "vertices": [],
                **extras,
            }
        )
        doc.appearance = restored.appearance
        doc.extensions = restored.extensions
        doc.geometry_templates = restored.geometry_templates
        return doc

    @staticmethod
    def get_custom_properties(
        city_object: BlenderObject, doc: CityJSONDocument, city_object_id: str
    ) -> None:
        """Creates a typed CityObject in doc and populates all its attributes from Blender custom properties."""
        # Collect all custom properties first so we know the type before constructing
        co_type = "GenericCityObject"
        props: list[tuple[list[str], Any]] = []
        for key, val in city_object.items():
            if key in {
                "_RNA_UI",
                CITYJSON_ID_PROPERTY,
                CITYJSON_GEOMETRY_PROPERTY,
            }:
                continue
            if isinstance(val, idprop.types.IDPropertyArray):
                val = val.to_list()
            split = key.split(".")
            if split[0] == "type" and isinstance(val, str):
                co_type = val
            else:
                props.append((split, val))

        # Preserve any geometry already appended by a preceding MESH object
        existing = doc.city_objects.get(city_object_id)
        existing_geometry = (
            existing.geometry
            if (existing is not None and hasattr(existing, "geometry"))
            else []
        )

        if co_type.startswith("+"):
            co = ExtensionObject(type=co_type)
        else:
            city_object_class = CITY_OBJECT_TYPES.get(co_type, GenericCityObject)
            co = city_object_class()
        if hasattr(co, "geometry"):
            co.geometry = existing_geometry
        doc.city_objects[city_object_id] = co

        # Apply collected properties to the typed CityObject
        for split, attribute in props:
            if split[0] == "attributes":
                target = co.attributes
                for part in split[1:-1]:
                    target = target.setdefault(part, {})
                target[split[-1]] = attribute
            elif split[0] == "members" and hasattr(co, "members"):
                if isinstance(attribute, list):
                    co.members = attribute
                else:
                    co.members.append(attribute)
            elif split[0] == "geographicalExtent":
                co.geographical_extent = attribute
            elif split[0] == "parents" and hasattr(co, "parents"):
                if isinstance(attribute, list):
                    co.parents = attribute
            elif split[0] == "children" and hasattr(co, "children"):
                if isinstance(attribute, list):
                    co.children = attribute

    @staticmethod
    def create_mesh_structure(
        city_object: BlenderObject, objid: str, doc: CityJSONDocument
    ) -> tuple[str, VertexCollection, PolygonCollection]:
        """Creates a typed geometry object and attaches it to the correct CityObject in doc."""
        stored_cityjson_id = city_object.get(CITYJSON_ID_PROPERTY)
        city_object_id = (
            stored_cityjson_id
            if isinstance(stored_cityjson_id, str)
            else objid.split(" ", maxsplit=2)[2]
        )

        # Validate lod custom property
        if "lod" not in city_object or not isinstance(city_object["lod"], str):
            print(
                "You either forgot to add `lod` as a custom property of the geometry, ",
                city_object.name,
                ", or 'lod' is not a string",
            )
            sys.exit(None)

        # Validate type custom property
        co_type = city_object.get("type", "")
        if co_type not in ("MultiSurface", "CompositeSurface", "Solid"):
            print(
                "You either forgot to add `type` as a custom property of the geometry, ",
                city_object.name,
                ", or 'type' is not `MultiSurface`, `CompositeSurface` or `Solid`",
            )
            sys.exit(None)

        geometry_class = GEOMETRY_PRIMITIVE_TYPES[co_type]
        geom = geometry_class(lod=city_object["lod"])
        if city_object.data.materials:
            geom.semantics = GeometrySemantics(surfaces=[], values=[[]])

        # Create a GenericCityObject placeholder if the EMPTY hasn't been processed yet
        if city_object_id not in doc.city_objects:
            doc.city_objects[city_object_id] = GenericCityObject()

        city_object_model = cast(GeometryContainer, doc.city_objects[city_object_id])
        city_object_model.geometry.append(geom)

        return city_object_id, city_object.data.vertices, city_object.data.polygons

    @staticmethod
    def export_geometry_and_semantics(
        city_object: BlenderObject,
        doc: CityJSONDocument,
        city_object_id: str,
        object_faces: PolygonCollection,
        object_verts: VertexCollection,
        vertex_indices: dict[tuple[float, float, float], int],
        cj_next_index: int,
    ) -> int:
        # Index in the geometry list that the new geometry needs to be stored
        city_object_model = cast(GeometryContainer, doc.city_objects[city_object_id])
        index = len(city_object_model.geometry) - 1
        geom = city_object_model.geometry[index]

        # Create semantic surfaces
        semantic_surfaces = store_semantic_surfaces(
            doc, city_object, index, city_object_id
        )

        if city_object["type"] in ("MultiSurface", "CompositeSurface"):
            for face in object_faces:
                geom.boundaries.append([[]])

                for i in range(len(object_faces[face.index].vertices)):
                    original_index = object_faces[face.index].vertices[i]
                    get_vertex = object_verts[original_index]

                    # Write vertex to CityJSON here so the world_matrix is always the
                    # correct one for each object.
                    write_vertices_to_cityjson(city_object, get_vertex.co, doc)
                    vertex_key = (
                        float(get_vertex.co[0]),
                        float(get_vertex.co[1]),
                        float(get_vertex.co[2]),
                    )
                    vertex_indices.setdefault(vertex_key, cj_next_index)
                    geom.boundaries[face.index][0].append(cj_next_index)
                    cj_next_index += 1

                link_face_semantic_surface(
                    doc, city_object, index, city_object_id, semantic_surfaces, face
                )

        if city_object["type"] == "Solid":
            geom.boundaries.append([])
            for face in object_faces:
                geom.boundaries[0].append([[]])
                for i in range(len(object_faces[face.index].vertices)):
                    original_index = object_faces[face.index].vertices[i]
                    get_vertex = object_verts[original_index]
                    vertex_key = (
                        float(get_vertex.co[0]),
                        float(get_vertex.co[1]),
                        float(get_vertex.co[2]),
                    )
                    if vertex_key in vertex_indices:
                        vert_index = vertex_indices[vertex_key]
                        geom.boundaries[0][face.index][0].append(vert_index)
                    else:
                        write_vertices_to_cityjson(city_object, get_vertex.co, doc)
                        vertex_indices[vertex_key] = cj_next_index
                        geom.boundaries[0][face.index][0].append(cj_next_index)
                        cj_next_index += 1

                link_face_semantic_surface(
                    doc, city_object, index, city_object_id, semantic_surfaces, face
                )

        return cj_next_index

    def execute(self) -> set[str]:
        start = time.time()
        print("\nExporting Blender scene into CityJSON file...")

        doc = self.initialize_document()
        progress_max = len(bpy.data.objects)
        cj_next_index = 0
        vertex_indices: dict[tuple[float, float, float], int] = {}

        objects = cast(Iterable[BlenderObject], bpy.data.objects)
        for progress, city_object in enumerate(objects, start=1):
            objid = get_cityjson_id(city_object)

            if CITYJSON_GEOMETRY_PROPERTY in city_object:
                serialized_geometry = city_object[CITYJSON_GEOMETRY_PROPERTY]
                if not isinstance(serialized_geometry, str):
                    raise TypeError("Preserved CityJSON geometry must be a JSON string")
                geometry_data = json.loads(serialized_geometry)
                geometry: GeometryModel
                if geometry_data.get("type") == "GeometryInstance":
                    geometry = GeometryInstance.from_dict(geometry_data)
                else:
                    geometry = geom_primitive_from_dict(geometry_data)
                if objid not in doc.city_objects:
                    doc.city_objects[objid] = GenericCityObject()
                city_object_model = cast(GeometryContainer, doc.city_objects[objid])
                city_object_model.geometry.append(geometry)

            # Empty objects contain the CityJSON attributes.
            elif city_object.type == "EMPTY":
                self.get_custom_properties(city_object, doc, objid)

            # Mesh objects contain the actual CityJSON geometries.
            elif city_object.type == "MESH":
                city_object_id, object_verts, object_faces = self.create_mesh_structure(
                    city_object, objid, doc
                )

                cj_next_index = self.export_geometry_and_semantics(
                    city_object,
                    doc,
                    city_object_id,
                    object_faces,
                    object_verts,
                    vertex_indices,
                    cj_next_index,
                )

            percentage = progress / progress_max * 100
            print(
                f"Appending geometries, vertices, semantics, attributes: "
                f"{percentage:.1f}% completed",
                end="\r",
            )

        if self.check_for_duplicates:
            remove_vertex_duplicates(doc, self.precision)
        export_parent_child(doc)
        export_transformation_parameters(doc)
        export_metadata(doc)

        print("Writing to CityJSON file...")
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False)

        end = time.time()
        timestamp = datetime.now(UTC)
        print(
            "\n[" + timestamp.strftime("%d/%b/%Y @ %H:%M:%S") + "]",
            "Blender scene successfully exported to CityJSON at '"
            + str(self.filepath)
            + "'.",
        )
        print("\nTotal exporting time: ", round(end - start, 2), "s")

        return {"FINISHED"}
