"""Module to manipulate objects in Blender regarding CityJSON"""

import json
import sys
import time
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol, cast

import bpy
import idprop

from ..models.city_objects import CITY_OBJECT_TYPES, GenericCityObject
from ..models.cityjson import CityJSONDocument
from ..models.geomprimitives import GEOMETRY_PRIMITIVE_TYPES, GeometrySemantics
from .blender_types import (
    BlenderObject,
    PolygonCollection,
    Vector,
    VertexCollection,
)
from .material import (
    BasicMaterialFactory,
    CityObjectTypeMaterialFactory,
    ReuseMaterialFactory,
    TypedCityObject,
)
from .utils import (
    assign_properties,
    clean_buffer,
    coord_translate_axis_origin,
    coord_translate_by_offset,
    create_empty_object,
    create_mesh_object,
    export_metadata,
    export_parent_child,
    export_transformation_parameters,
    get_collection,
    get_geometry_name,
    link_face_semantic_surface,
    remove_scene_objects,
    remove_vertex_duplicates,
    store_semantic_surfaces,
    write_vertices_to_cityjson,
)


class GeometryContainer(Protocol):
    geometry: list[Any]


class ParsedCityObject(TypedCityObject, Protocol):
    parents: list[str]

    def to_dict(self) -> dict[str, Any]: ...


MaterialFactory = (
    BasicMaterialFactory | ReuseMaterialFactory | CityObjectTypeMaterialFactory
)


class CityJSONParser:
    """Class that parses a CityJSON file to Blender"""

    def __init__(
        self,
        filepath: str,
        material_type: str,
        reuse_materials: bool = True,
        clear_scene: bool = True,
    ) -> None:
        self.filepath = filepath
        self.clear_scene = clear_scene

        self.data: dict[str, Any] = {}
        self.document: CityJSONDocument | None = None
        self.vertices: Sequence[Sequence[float]] = ()
        self.material_factory: MaterialFactory

        if material_type == "SURFACES":
            if reuse_materials:
                self.material_factory = ReuseMaterialFactory()
            else:
                self.material_factory = BasicMaterialFactory()
        else:
            self.material_factory = CityObjectTypeMaterialFactory()

    def load_data(self) -> None:
        """Loads the CityJSON data from the file"""

        with open(self.filepath) as json_file:
            self.data = json.load(json_file)
        self.document = CityJSONDocument.from_dict(self.data)

    def prepare_vertices(self) -> None:
        """Prepares the vertices by applying any required transformations"""

        vertices: list[tuple[float, float, float]] = []

        if self.document is None:
            raise RuntimeError("CityJSON data must be loaded before preparing vertices")

        transform = self.document.transform

        # Checking if coordinates need to be transformed and
        # transforming if necessary
        if transform is None:
            for vertex in self.document.vertices:
                vertices.append((float(vertex[0]), float(vertex[1]), float(vertex[2])))
        else:
            # Transforming coords to actual real world coords
            for vertex in self.document.vertices:
                x = vertex[0] * transform.scale[0] + transform.translate[0]
                y = vertex[1] * transform.scale[1] + transform.translate[1]
                z = vertex[2] * transform.scale[2] + transform.translate[2]

                vertices.append((x, y, z))
            # Creating transform properties
            bpy.context.scene.world["transformed"] = True
            bpy.context.scene.world["transform.X_scale"] = transform.scale[0]
            bpy.context.scene.world["transform.Y_scale"] = transform.scale[1]
            bpy.context.scene.world["transform.Z_scale"] = transform.scale[2]

            bpy.context.scene.world["transform.X_translate"] = transform.translate[0]
            bpy.context.scene.world["transform.Y_translate"] = transform.translate[1]
            bpy.context.scene.world["transform.Z_translate"] = transform.translate[2]

        if "Axis_Origin_X_translation" in bpy.context.scene.world:
            offx = -bpy.context.scene.world["Axis_Origin_X_translation"]
            offy = -bpy.context.scene.world["Axis_Origin_Y_translation"]
            offz = -bpy.context.scene.world["Axis_Origin_Z_translation"]
            translation = coord_translate_by_offset(vertices, offx, offy, offz)
        else:
            translation = coord_translate_axis_origin(vertices)

            bpy.context.scene.world["Axis_Origin_X_translation"] = -translation[1]
            bpy.context.scene.world["Axis_Origin_Y_translation"] = -translation[2]
            bpy.context.scene.world["Axis_Origin_Z_translation"] = -translation[3]

        # Updating vertices with new translated vertices
        self.vertices = translation[0]

    def parse_geometry(
        self, theid: str, obj: ParsedCityObject, geom: Any, index: int
    ) -> BlenderObject:
        """Returns a mesh object for the provided geometry"""
        bound = []

        # Checking how nested the geometry is i.e what kind of 3D
        # geometry it contains
        if geom.type in ("MultiSurface", "CompositeSurface"):
            for face in geom.boundaries:
                if face:
                    bound.append(tuple(face[0]))
        elif geom.type == "Solid":
            for shell in geom.boundaries:
                for face in shell:
                    if face:
                        bound.append(tuple(face[0]))
        elif geom.type == "MultiSolid":
            for solid in geom.boundaries:
                for shell in solid:
                    for face in shell:
                        if face:
                            bound.append(tuple(face[0]))

        temp_vertices, temp_bound = clean_buffer(self.vertices, bound)

        mats, values = self.material_factory.get_materials(
            city_object=obj, geometry=geom
        )

        geom_obj = create_mesh_object(
            get_geometry_name(theid, geom, index),
            temp_vertices,
            temp_bound,
            mats,
            values,
        )

        if geom.type != "GeometryInstance":
            geom_obj["lod"] = str(geom.lod)

        geom_obj["type"] = geom.type

        return geom_obj

    def execute(self) -> set[str]:
        """Execute the import process"""

        if self.clear_scene:
            remove_scene_objects()

        print("\nImporting CityJSON file...")

        self.load_data()

        self.prepare_vertices()

        if self.document is None:
            raise RuntimeError("CityJSON data was not loaded")
        doc = self.document

        # Storing the reference system
        metadata = doc.metadata
        if metadata is not None and metadata.reference_system is not None:
            bpy.context.scene.world["CRS"] = metadata.reference_system

        new_objects = []
        city_objects = {}

        progress_max = len(doc.city_objects)
        progress = 0
        start_import = time.time()

        # Creating empty meshes for every CityObjects and linking its
        # geometries as children-meshes
        for progress, (objid, obj_value) in enumerate(
            doc.city_objects.items(), start=1
        ):
            obj = cast(ParsedCityObject, obj_value)
            city_object = create_empty_object(objid)
            city_object = assign_properties(city_object, obj.to_dict())
            new_objects.append(city_object)
            city_objects[objid] = city_object

            geometry_owner = cast(GeometryContainer, obj_value)
            for geometry_index, geometry in enumerate(geometry_owner.geometry):
                geom_obj = self.parse_geometry(objid, obj, geometry, geometry_index)
                geom_obj.parent = city_object
                new_objects.append(geom_obj)

            percentage = progress / progress_max * 100
            print(f"Importing: {percentage:.1f}% completed", end="\r")

        end_import = time.time()

        start_hierarchy = time.time()

        # Assign child building parts to parent buildings.
        print("\nBuilding hierarchy...")

        for progress, (objid, obj_value) in enumerate(
            doc.city_objects.items(), start=1
        ):
            obj = cast(ParsedCityObject, obj_value)
            if obj.parents:
                parent_id = obj.parents[0]
                city_objects[objid].parent = city_objects[parent_id]

            percentage = progress / progress_max * 100
            print(f"Building hierarchy: {percentage:.1f}% completed", end="\r")

        end_hierarchy = time.time()

        start_link = time.time()

        # Link everything to the scene
        print("\nLinking objects to the scene...")
        collection = bpy.context.scene.collection
        for new_object in new_objects:
            if "lod" in new_object:
                get_collection("LoD{}".format(new_object["lod"])).objects.link(
                    new_object
                )
            else:
                collection.objects.link(new_object)

        end_link = time.time()
        # Console output
        print("Total importing time: ", round(end_import - start_import, 2), "s")
        print("Building hierarchy: ", round(end_hierarchy - start_hierarchy, 2), "s")
        print("Linking: ", round(end_link - start_link, 2), "s")
        print("Done!")
        timestamp = datetime.now(UTC)
        print(
            "\n[" + timestamp.strftime("%d/%b/%Y @ %H:%M:%S") + "]",
            "CityJSON file successfully imported from '" + str(self.filepath) + "'.",
        )

        return {"FINISHED"}


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
        return CityJSONDocument()

    @staticmethod
    def get_custom_properties(
        city_object: BlenderObject, doc: CityJSONDocument, city_object_id: str
    ) -> None:
        """Creates a typed CityObject in doc and populates all its attributes from Blender custom properties."""
        # Collect all custom properties first so we know the type before constructing
        co_type = "GenericCityObject"
        props: list[tuple[list[str], Any]] = []
        for key, val in city_object.items():
            if key == "_RNA_UI":
                continue
            if isinstance(val, idprop.types.IDPropertyArray):
                val = val.to_list()
            split = key.split(".")
            if split[0] == "type" and isinstance(val, str):
                co_type = val
            else:
                props.append((split, val))

        city_object_class = CITY_OBJECT_TYPES.get(co_type, GenericCityObject)

        # Preserve any geometry already appended by a preceding MESH object
        existing = doc.city_objects.get(city_object_id)
        existing_geometry = (
            existing.geometry
            if (existing is not None and hasattr(existing, "geometry"))
            else []
        )

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
        city_object_id = objid.split(" ")[2]

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
        vertices: list[Vector],
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
                    vertices.append(get_vertex.co)
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
                    if get_vertex.co in vertices:
                        vert_index = vertices.index(get_vertex.co)
                        geom.boundaries[0][face.index][0].append(vert_index)
                    else:
                        write_vertices_to_cityjson(city_object, get_vertex.co, doc)
                        vertices.append(get_vertex.co)
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
        verts: list[Vector] = []

        objects = cast(Iterable[BlenderObject], bpy.data.objects)
        for progress, city_object in enumerate(objects, start=1):
            objid = city_object.name

            # Empty objects contain the CityJSON attributes.
            if city_object.type == "EMPTY":
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
                    verts,
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
