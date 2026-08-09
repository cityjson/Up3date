"""Module to manipulate objects in Blender regarding CityJSON"""

import json
import sys
import time
from datetime import UTC, datetime

import bpy
import idprop

from ..models.cityjson import CityJSON
from .material import (
    BasicMaterialFactory,
    CityObjectTypeMaterialFactory,
    ReuseMaterialFactory,
)
from .utils import (
    assign_properties,
    clean_buffer,
    coord_translate_axis_origin,
    coord_translate_by_offset,
    create_empty_object,
    create_mesh_object,
    export_attributes,
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


class CityJSONParser:
    """Class that parses a CityJSON file to Blender"""

    def __init__(self, filepath, material_type, reuse_materials=True, clear_scene=True):
        self.filepath = filepath
        self.clear_scene = clear_scene

        self.data = {}
        self.vertices = []

        if material_type == "SURFACES":
            if reuse_materials:
                self.material_factory = ReuseMaterialFactory()
            else:
                self.material_factory = BasicMaterialFactory()
        else:
            self.material_factory = CityObjectTypeMaterialFactory()

    def load_data(self):
        """Loads the CityJSON data from the file"""

        with open(self.filepath) as json_file:
            self.data = json.load(json_file)

    def prepare_vertices(self):
        """Prepares the vertices by applying any required transformations"""

        vertices = []

        # Checking if coordinates need to be transformed and
        # transforming if necessary
        if "transform" not in self.data:
            for vertex in self.data["vertices"]:
                vertices.append(tuple(vertex))
        else:
            trans_param = self.data["transform"]
            # Transforming coords to actual real world coords
            for vertex in self.data["vertices"]:
                x = vertex[0] * trans_param["scale"][0] + trans_param["translate"][0]
                y = vertex[1] * trans_param["scale"][1] + trans_param["translate"][1]
                z = vertex[2] * trans_param["scale"][2] + trans_param["translate"][2]

                vertices.append((x, y, z))
            # Creating transform properties
            bpy.context.scene.world["transformed"] = True
            bpy.context.scene.world["transform.X_scale"] = trans_param["scale"][0]
            bpy.context.scene.world["transform.Y_scale"] = trans_param["scale"][1]
            bpy.context.scene.world["transform.Z_scale"] = trans_param["scale"][2]

            bpy.context.scene.world["transform.X_translate"] = trans_param["translate"][
                0
            ]
            bpy.context.scene.world["transform.Y_translate"] = trans_param["translate"][
                1
            ]
            bpy.context.scene.world["transform.Z_translate"] = trans_param["translate"][
                2
            ]

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

    def parse_geometry(self, theid: str, obj: dict, geom, index):
        """Returns a mesh object for the provided geometry"""
        bound = []

        # Checking how nested the geometry is i.e what kind of 3D
        # geometry it contains
        if geom["type"] == "MultiSurface" or geom["type"] == "CompositeSurface":
            for face in geom["boundaries"]:
                if face:
                    bound.append(tuple(face[0]))
        elif geom["type"] == "Solid":
            for shell in geom["boundaries"]:
                for face in shell:
                    if face:
                        bound.append(tuple(face[0]))
        elif geom["type"] == "MultiSolid":
            for solid in geom["boundaries"]:
                for shell in solid:
                    for face in shell:
                        if face:
                            bound.append(tuple(face[0]))

        temp_vertices, temp_bound = clean_buffer(self.vertices, bound)

        mats, values = self.material_factory.get_materials(
            cityobject=obj, geometry=geom
        )

        geom_obj = create_mesh_object(
            get_geometry_name(theid, geom, index),
            temp_vertices,
            temp_bound,
            mats,
            values,
        )

        if "lod" in geom:
            geom_obj["lod"] = int(geom["lod"])

        geom_obj["type"] = geom["type"]

        return geom_obj

    def execute(self):
        """Execute the import process"""

        if self.clear_scene:
            remove_scene_objects()

        print("\nImporting CityJSON file...")

        self.load_data()

        self.prepare_vertices()

        # Storing the reference system
        metadata = self.data.get("metadata", {})
        if "referenceSystem" in metadata:
            bpy.context.scene.world["CRS"] = metadata["referenceSystem"]

        new_objects = []
        cityobjs = {}

        progress_max = len(self.data["CityObjects"])
        progress = 0
        start_import = time.time()

        # Creating empty meshes for every CityObjects and linking its
        # geometries as children-meshes
        for progress, (objid, obj) in enumerate(
            self.data["CityObjects"].items(), start=1
        ):
            cityobject = create_empty_object(objid)
            cityobject = assign_properties(cityobject, obj)
            new_objects.append(cityobject)
            cityobjs[objid] = cityobject

            for geometry_index, geometry in enumerate(obj["geometry"]):
                geom_obj = self.parse_geometry(objid, obj, geometry, geometry_index)
                geom_obj.parent = cityobject
                new_objects.append(geom_obj)

            percentage = progress / progress_max * 100
            print(f"Importing: {percentage:.1f}% completed", end="\r")

        end_import = time.time()

        start_hierarchy = time.time()

        # Assign child building parts to parent buildings.
        print("\nBuilding hierarchy...")

        for progress, (objid, obj) in enumerate(
            self.data["CityObjects"].items(), start=1
        ):
            if "parents" in obj:
                parent_id = obj["parents"][0]
                cityobjs[objid].parent = cityobjs[parent_id]

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
    def __init__(self, filepath, check_for_duplicates=True, precision=3):
        self.filepath = filepath
        self.check_for_duplicates = check_for_duplicates
        self.precision = precision

    @staticmethod
    def initialize_dictionary() -> CityJSON:
        return {
            "type": "CityJSON",
            "version": "1.0",
            # "extensions": {},
            "metadata": {},
            "CityObjects": {},
            "vertices": [],
            # "appearance":{}
        }

    @staticmethod
    def get_custom_properties(city_object, init_json, city_object_id):
        """Creates the required structure according to CityJSON and writes all the object's custom properties (aka attributes)"""
        init_json["CityObjects"].setdefault(city_object_id, {})
        init_json["CityObjects"][city_object_id].setdefault("geometry", [])
        cp = city_object.items()
        for prop in cp:
            # When a new empty object is added by user, Blender assigns some built in properties at the first index of the property list.
            # With this it is bypassed and continues to the actual properties of the object
            if prop[0] == "_RNA_UI":
                continue
            # Upon import into Blender the for every level deeper an attribute is nested the more a "." is used in the string between the 2 attributes' names
            # So to store it back to the original form the concatenated string must be split.
            # Split is the list containing the original attributes names.
            split = prop[0].split(".")
            # Check if the attribute is IDPropertyArray and convert to python list type because JSON encoder cannot handle type IDPropertyArray.
            if isinstance(prop[1], idprop.types.IDPropertyArray):
                attribute = prop[1].to_list()
            else:
                attribute = prop[1]
            export_attributes(split, init_json, city_object_id, attribute)

    @staticmethod
    def create_mesh_structure(city_object, objid, init_json):
        "Prepares the structure within the empty mesh for storing the geometries, stored the lod and accesses the vertices and faces of the geometry within Blender"
        # Create geometry key within the empty object for storing the LoD(s)
        city_object_id = objid.split(" ")[2]
        init_json["CityObjects"].setdefault(city_object_id, {})
        init_json["CityObjects"][city_object_id].setdefault("geometry", [])
        # Check if the user has assigned the custom properties 'lod' and 'type' correctly
        if "lod" in city_object and (
            type(city_object["lod"]) == float or type(city_object["lod"]) == int
        ):
            if "type" in city_object and (
                city_object["type"] == "MultiSurface"
                or city_object["type"] == "CompositeSurface"
                or city_object["type"] == "Solid"
            ):
                # Check if object has materials (in Blender) i.e semantics in real life and if yes create the extra keys (within_geometry) to store it.
                # Otherwise just create the rest of the tags
                if city_object.data.materials:
                    init_json["CityObjects"][city_object_id]["geometry"].append(
                        {
                            "type": city_object["type"],
                            "boundaries": [],
                            "semantics": {"surfaces": [], "values": [[]]},
                            "texture": {},
                            "lod": city_object["lod"],
                        }
                    )
                else:
                    init_json["CityObjects"][city_object_id]["geometry"].append(
                        {
                            "type": city_object["type"],
                            "boundaries": [],
                            "lod": city_object["lod"],
                        }
                    )
            else:
                print(
                    "You either forgot to add `type` as a custom property of the geometry, ",
                    city_object.name,
                    ", or 'type' is not `MultiSurface`,`CompositeSurface` or `Solid`",
                )
                sys.exit(None)
        else:
            print(
                "You either forgot to add `lod` as a custom property of the geometry, ",
                city_object.name,
                ", or 'lod' is not a number",
            )
            sys.exit(None)

        # Accessing object's vertices
        object_verts = city_object.data.vertices
        # Accessing object's faces
        object_faces = city_object.data.polygons

        return city_object_id, object_verts, object_faces

    @staticmethod
    def export_geometry_and_semantics(
        city_object,
        init_json,
        city_object_id,
        object_faces,
        object_verts,
        vertices,
        cj_next_index,
    ):
        # Index in the geometry list that the new geometry needs to be stored.
        index = len(init_json["CityObjects"][city_object_id]["geometry"]) - 1

        # Create semantic surfaces
        semantic_surfaces = store_semantic_surfaces(
            init_json, city_object, index, city_object_id
        )
        if (
            city_object["type"] == "MultiSurface"
            or city_object["type"] == "CompositeSurface"
        ):
            # Browsing through faces and their vertices of every object.
            for face in object_faces:
                init_json["CityObjects"][city_object_id]["geometry"][index][
                    "boundaries"
                ].append([[]])

                for i in range(len(object_faces[face.index].vertices)):
                    original_index = object_faces[face.index].vertices[i]
                    get_vertex = object_verts[original_index]

                    # Write vertex to CityJSON at this point so the mesh_object.world_matrix (aka transformation matrix) is always the
                    # correct one. With the previous way it would take the last object's transformation matrix and would potentially lead to wrong final
                    # coordinate to be exported.
                    write_vertices_to_cityjson(city_object, get_vertex.co, init_json)
                    vertices.append(get_vertex.co)
                    init_json["CityObjects"][city_object_id]["geometry"][index][
                        "boundaries"
                    ][face.index][0].append(cj_next_index)
                    cj_next_index += 1

                # In case the object has semantics they are accordingly stored as well
                link_face_semantic_surface(
                    init_json,
                    city_object,
                    index,
                    city_object_id,
                    semantic_surfaces,
                    face,
                )

        if city_object["type"] == "Solid":
            init_json["CityObjects"][city_object_id]["geometry"][index][
                "boundaries"
            ].append([])
            for face in object_faces:
                init_json["CityObjects"][city_object_id]["geometry"][index][
                    "boundaries"
                ][0].append([[]])
                for i in range(len(object_faces[face.index].vertices)):
                    original_index = object_faces[face.index].vertices[i]
                    get_vertex = object_verts[original_index]
                    if get_vertex.co in vertices:
                        vert_index = vertices.index(get_vertex.co)
                        init_json["CityObjects"][city_object_id]["geometry"][index][
                            "boundaries"
                        ][0][face.index][0].append(vert_index)
                    else:
                        write_vertices_to_cityjson(
                            city_object, get_vertex.co, init_json
                        )
                        vertices.append(get_vertex.co)
                        init_json["CityObjects"][city_object_id]["geometry"][index][
                            "boundaries"
                        ][0][face.index][0].append(cj_next_index)
                        cj_next_index += 1
                # In case the object has semantics they are accordingly stored as well
                link_face_semantic_surface(
                    init_json,
                    city_object,
                    index,
                    city_object_id,
                    semantic_surfaces,
                    face,
                )
        return cj_next_index

    def execute(self):
        start = time.time()
        print("\nExporting Blender scene into CityJSON file...")

        init_json: CityJSON = self.initialize_dictionary()
        progress_max = len(bpy.data.objects)
        cj_next_index = 0
        verts = []

        for progress, city_object in enumerate(bpy.data.objects, start=1):
            objid = city_object.name

            # Empty objects contain the CityJSON attributes.
            if city_object.type == "EMPTY":
                self.get_custom_properties(city_object, init_json, objid)

            # Mesh objects contain the actual CityJSON geometries.
            elif city_object.type == "MESH":
                (
                    city_object_id,
                    object_verts,
                    object_faces,
                ) = self.create_mesh_structure(
                    city_object,
                    objid,
                    init_json,
                )

                cj_next_index = self.export_geometry_and_semantics(
                    city_object,
                    init_json,
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
            remove_vertex_duplicates(init_json, self.precision)
        export_parent_child(init_json)
        export_transformation_parameters(init_json)
        export_metadata(init_json)

        print("Writing to CityJSON file...")
        # Writing CityJSON file
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(init_json, f, ensure_ascii=False)

        end = time.time()
        timestamp = datetime.now(UTC)
        print(
            "\n[" + timestamp.strftime("%d/%b/%Y @ %H:%M:%S") + "]",
            "Blender scene successfully exported to CityJSON at '"
            + str(self.filepath)
            + "'.",
        )
        # print("\nBlender scene successfully exported to CityJSON at '"+str(self.filepath)+"'.")
        print("\nTotal exporting time: ", round(end - start, 2), "s")

        return {"FINISHED"}
