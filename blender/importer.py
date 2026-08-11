"""Module to manipulate objects in Blender regarding CityJSON"""

import json
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Protocol, TypeAlias, cast

import bpy

from ..models.cityjson import CityJSONDocument
from ..models.geomprimitives import (
    GeometryPrimitive,
)
from ..models.geomtemplates import GeometryInstance
from .blender_types import (
    BlenderObject,
)
from .cityjson_utils import (
    clean_buffer,
    coord_translate_axis_origin,
    coord_translate_by_offset,
    get_geometry_name,
)
from .material import (
    BasicMaterialFactory,
    CityObjectTypeMaterialFactory,
    ReuseMaterialFactory,
    TypedCityObject,
)
from .scene import (
    CITYJSON_DOCUMENT_EXTRAS_PROPERTY,
    CITYJSON_GEOMETRY_PROPERTY,
    CITYJSON_ID_PROPERTY,
    assign_properties,
    create_empty_object,
    create_mesh_object,
    get_collection,
    remove_scene_objects,
)


class GeometryContainer(Protocol):
    geometry: list[Any]


class ParsedCityObject(TypedCityObject, Protocol):
    parents: list[str]

    def to_dict(self) -> dict[str, Any]: ...


MaterialFactory = (
    BasicMaterialFactory | ReuseMaterialFactory | CityObjectTypeMaterialFactory
)

GeometryModel: TypeAlias = GeometryPrimitive | GeometryInstance


class CityJSONImporter:
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
            x_scale = transform.scale[0] or 1
            y_scale = transform.scale[1] or 1
            z_scale = transform.scale[2] or 1
            for vertex in self.document.vertices:
                x = vertex[0] * x_scale + transform.translate[0]
                y = vertex[1] * y_scale + transform.translate[1]
                z = vertex[2] * z_scale + transform.translate[2]

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
        self, theid: str, obj: ParsedCityObject, geom: GeometryModel, index: int
    ) -> BlenderObject:
        """Returns a mesh object for the provided geometry"""
        if geom.type not in {"MultiSurface", "CompositeSurface", "Solid"}:
            geom_obj = create_empty_object(get_geometry_name(theid, geom, index))
            geom_obj[CITYJSON_GEOMETRY_PROPERTY] = json.dumps(geom.to_dict())
            geom_obj["type"] = geom.type
            if hasattr(geom, "lod"):
                geom_obj["lod"] = str(geom.lod)
            return geom_obj

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

        document_extras: dict[str, Any] = {}
        if doc.extensions:
            document_extras["extensions"] = doc.extensions
        if doc.appearance is not None:
            document_extras["appearance"] = doc.appearance.to_dict()
        if doc.geometry_templates is not None:
            document_extras["geometry-templates"] = doc.geometry_templates.to_dict()
        if document_extras:
            bpy.context.scene.world[CITYJSON_DOCUMENT_EXTRAS_PROPERTY] = json.dumps(
                document_extras
            )

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
            city_object[CITYJSON_ID_PROPERTY] = objid
            city_object = assign_properties(city_object, obj.to_dict())
            new_objects.append(city_object)
            city_objects[objid] = city_object

            geometry_owner = cast(GeometryContainer, obj_value)
            for geometry_index, geometry in enumerate(geometry_owner.geometry):
                geom_obj = self.parse_geometry(objid, obj, geometry, geometry_index)
                geom_obj[CITYJSON_ID_PROPERTY] = objid
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
