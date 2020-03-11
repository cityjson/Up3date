"""Module to manipulate objects in Blender regarding CityJSON"""

import json
import time

import bpy
import idprop

from .material import (BasicMaterialFactory, ReuseMaterialFactory,
                       CityObjectTypeMaterialFactory)
from .utils import (assign_properties, clean_buffer, clean_list,
                    coord_translate_axis_origin, remove_scene_objects,
                    write_vertices_to_CityJSON,
                    export_transformation_parameters, export_metadata,
                    export_parent_child,export_attributes,store_semantics)

def cityJSON_exporter(context, filepath):
    start=time.time()
    print("\nExporting Blender scene into CityJSON file...")
    #Create the initial structure of the cityjson dictionary
    minimal_json = {
        "type": "CityJSON",
        "version": "1.0",
        # "extensions": {},
        "metadata": {},
        "CityObjects": {},
        "vertices":[],
        #"appearance":{}
    }
    # Variables to keep up with the exporting progress. Used to print percentage in the terminal.
    progress_max = len(bpy.data.objects)
    # Initialize progress status
    progress = 0
    # Variable to store the next index free that a vertex should be saved in the cityjson file. Avoiding saving duplicates.
    cityjson_vertices_index = 0
    # Create a list of vertices to store the global vertices of all objects
    vertices = list()
    for city_object in bpy.data.objects:
        #Empty objects have all the attributes so their properties are accessed to extract this information
        if city_object.type=='EMPTY':
            name=city_object.name
            minimal_json["CityObjects"].setdefault(name,{})
            minimal_json["CityObjects"][name].setdefault('geometry',[])

            #Get all the custom properties of the object
            cp=city_object.items()
            for prop in cp:
                # Upon import into Blender the for every level deeper an attribute is nested the more a "." is used in the string between the 2 attributes' names
                # So to store it back to the original form the concatenated string must be split. 
                # Split is the list containing the original attributes names.
                split = prop[0].split(".")                
                # Check if the attribute is IDPropertyArray and convert to python list type because JSON encoder cannot handle type IDPropertyArray.
                if isinstance(prop[1],idprop.types.IDPropertyArray):
                    attribute=prop[1].to_list()
                else:
                    attribute=prop[1]

                export_attributes(split,minimal_json,name,attribute)           
                      
        #If the object is MESH means that is an actual geometry contained in the CityJSON file
        if city_object.type =='MESH':
            """ Export geometries with their semantics into CityJSON
                Geometry type is checked for every object, because the structure that the geometry has to be stored in the cityjson is different depending on the geometry type 
                In case the object has semantics they are accordingly stored as well using the 'store_semantics' function
                Case of multisolid hasn't been taken under consideration!!
           """
            name = city_object.name
            original_objects_name = name[10:]
            minimal_json["CityObjects"].setdefault(original_objects_name,{})
            minimal_json["CityObjects"][original_objects_name].setdefault('geometry',[])
                               
            #Create multiple geometries for multiple LoDs 
            #Check if object has materials (in Blender) i.e semantics in real life and if yes create the extra tags to store it.
            #Otherwise just create the rest of the tags
            if city_object.data.materials:
                minimal_json["CityObjects"][original_objects_name]['geometry'].append({'type':city_object['type'],'boundaries':[],'semantics':{},'texture':{},'lod':city_object['lod']})
            else:
                minimal_json["CityObjects"][original_objects_name]['geometry'].append({'type':city_object['type'],'boundaries':[],'lod':city_object['lod']})
        
            #Accessing specific object's vertices coordinates 
            specific_object_verts = city_object.data.vertices
            #Accessing specific object's faces
            specific_object_faces = city_object.data.polygons

            #Index in the geometry list that the new geometry needs to be stored.
            index = len(minimal_json["CityObjects"][original_objects_name]['geometry'])-1
                        
            if city_object['type'] == 'MultiSurface' or city_object['type'] == 'CompositeSurface' :
                # Browsing through faces and their vertices of every object.
                for face in specific_object_faces:
                    minimal_json["CityObjects"][original_objects_name]["geometry"][index]["boundaries"].append([[]])
                    
                    for i in range(len(specific_object_faces[face.index].vertices)):
                        original_index = specific_object_faces[face.index].vertices[i]
                        get_vertex = specific_object_verts[original_index]
                        # Check if vertex already is saved.
                        # If yes append its index at the vertices list into the cityjson file.
                        # If no append this vertex in the vertices list then append its vertex (cityjson_vertices_index) and increment this index by one.
                        if get_vertex.co in vertices:    
                            vert_index = vertices.index(get_vertex.co)
                            minimal_json["CityObjects"][original_objects_name]["geometry"][index]["boundaries"][face.index][0].append(vert_index)
                        else:
                            vertices.append(get_vertex.co)
                            minimal_json["CityObjects"][original_objects_name]["geometry"][index]["boundaries"][face.index][0].append(cityjson_vertices_index)
                            cityjson_vertices_index += 1
                    # In case the object has semantics they are accordingly stored as well
                    store_semantics(minimal_json,city_object,index,original_objects_name,face)

            if city_object['type'] == 'Solid':
                minimal_json["CityObjects"][original_objects_name]["geometry"][index]["boundaries"].append([])
                for face in specific_object_faces:
                    minimal_json["CityObjects"][original_objects_name]["geometry"][index]["boundaries"][0].append([[]])
                    for i in range(len(specific_object_faces[face.index].vertices)):
                        original_index = specific_object_faces[face.index].vertices[i]
                        
                        get_vertex = specific_object_verts[original_index]
                        if get_vertex.co in vertices:
                            vert_index = vertices.index(get_vertex.co)
                            minimal_json["CityObjects"][original_objects_name]["geometry"][index]["boundaries"][0][face.index][0].append(vert_index)
                        else:
                            vertices.append(get_vertex.co)
                            minimal_json["CityObjects"][original_objects_name]["geometry"][index]["boundaries"][0][face.index][0].append(cityjson_vertices_index)
                            cityjson_vertices_index += 1
                    # In case the object has semantics they are accordingly stored as well
                    store_semantics(minimal_json,city_object,index,original_objects_name,face)
                    
        progress += 1
        print("Appending geometries, semantics, attributes: {percent}% completed".format(percent=round(progress * 100 / progress_max, 1)),end="\r")
        
    export_parent_child(minimal_json)
    write_vertices_to_CityJSON(city_object,minimal_json,vertices,len(vertices))
    export_transformation_parameters(minimal_json)
    export_metadata(minimal_json)
            
    print ("Writing to CityJSON file...")
    #Writing CityJSON file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(minimal_json, f, ensure_ascii=False)
    
    end=time.time()
    print("\nBlender scene successfully exported to CityJSON at '"+str(filepath)+"'.")
    print("\nTotal exporting time: ", round(end-start, 2), "s")
      
    return{'FINISHED'}       

def get_geometry_name(objid, geom, index):
    """Returns the name of the provided geometry"""
    if 'lod' in geom:
        return "{index}: [LoD{lod}] {name}".format(name=objid, lod=geom['lod'], index=index)
    else:
        return "{index}: [GeometryInstance] {name}".format(name=objid, index=index)

def create_empty_object(name):
    """Returns an empty blender object"""

    new_object = bpy.data.objects.new(name, None)

    return new_object

def create_mesh_object(name, vertices, faces, materials=[], material_indices=[]):
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
            print("Object {name} has {num_faces} faces but {num_surfaces} semantic surfaces!"
                  .format(name=name,
                          num_faces=len(faces),
                          num_surfaces=len(material_indices)))

        mesh_data.update()

    new_object = bpy.data.objects.new(name, mesh_data)

    return new_object

def get_collection(collection_name):
    """Returns a collection with the given name"""

    if collection_name in bpy.data.collections:
        return bpy.data.collections[collection_name]
    
    new_collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(new_collection)

    return new_collection

class CityJSONParser:
    """Class that parses a CityJSON file to Blender"""

    def __init__(self, filepath, material_type, reuse_materials=True, clear_scene=True, origin_text=True):
        self.filepath = filepath
        self.clear_scene = clear_scene
        self.origin_text = origin_text

        self.data = {}
        self.vertices = []

        if material_type == 'SURFACES':
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
        if 'transform' not in self.data:
            for vertex in self.data['vertices']:
                vertices.append(tuple(vertex))
        else:
            trans_param = self.data['transform']
            # Transforming coords to actual real world coords
            for vertex in self.data['vertices']:
                x = vertex[0]*trans_param['scale'][0] \
                    + trans_param['translate'][0]
                y = vertex[1]*trans_param['scale'][1] \
                    + trans_param['translate'][1]
                z = vertex[2]*trans_param['scale'][2] \
                    + trans_param['translate'][2]

                vertices.append((x, y, z))
            #Creating transform properties
            bpy.context.scene.world['transformed'] = True
            bpy.context.scene.world['transform.X_scale'] = trans_param['scale'][0]
            bpy.context.scene.world['transform.Y_scale'] = trans_param['scale'][1]
            bpy.context.scene.world['transform.Z_scale'] = trans_param['scale'][2]

            bpy.context.scene.world['transform.X_translate'] = trans_param['translate'][0]
            bpy.context.scene.world['transform.Y_translate'] = trans_param['translate'][1]
            bpy.context.scene.world['transform.Z_translate'] = trans_param['translate'][2]

        # Translating coordinates to the axis origin
        translation = coord_translate_axis_origin(vertices)

        bpy.context.scene.world['Axis_Origin_X_translation']=-translation[1]
        bpy.context.scene.world['Axis_Origin_Y_translation']=-translation[2]
        bpy.context.scene.world['Axis_Origin_Z_translation']=-translation[3]
        
        # Showing origin coord.
        print("CRS position : X: {x} ; Y: {y} ; Z: {z}".format(x=translation[1],y=translation[2],z=translation[3]))

        if self.origin_text:
            bpy.ops.object.text_add(location=(0,0,0))
            originxyz=bpy.context.object
            originxyz.name = "_OriginXYZ"
            originxyz.data.name = "X: {x} ; Y: {y} ; Z: {z}".format(x=translation[1],y=translation[2],z=translation[3])
            originxyz.data.body = originxyz.data.name

        # Updating vertices with new translated vertices
        self.vertices = translation[0]

    def parse_geometry(self, theid, obj, geom, index):
        """Returns a mesh object for the provided geometry"""
        bound = []

        # Checking how nested the geometry is i.e what kind of 3D
        # geometry it contains
        if (geom['type'] == 'MultiSurface'
                or geom['type'] == 'CompositeSurface'):
            for face in geom['boundaries']:
                if face:
                    bound.append(tuple(face[0]))
        elif geom['type'] == 'Solid':
            for shell in geom['boundaries']:
                for face in shell:
                    if face:
                        bound.append(tuple(face[0]))
        elif geom['type'] == 'MultiSolid':
            for solid in geom['boundaries']:
                for shell in solid:
                    for face in shell:
                        if face:
                            bound.append(tuple(face[0]))

        temp_vertices, temp_bound = clean_buffer(self.vertices, bound)

        mats, values = self.material_factory.get_materials(cityobject=obj,
                                                           geometry=geom)

        geom_obj = create_mesh_object(get_geometry_name(theid, geom, index),
                                      temp_vertices,
                                      temp_bound,
                                      mats,
                                      values)

        if 'lod' in geom:
            geom_obj['lod'] = geom['lod']

        geom_obj['type'] = geom['type']

        return geom_obj

    def execute(self):
        """Execute the import process"""

        if self.clear_scene:
            remove_scene_objects()
            
        print("\nImporting CityJSON file...")

        self.load_data()

        self.prepare_vertices()

        #Storing the reference system        
        if 'referenceSystem' in self.data['metadata']:
            bpy.context.scene.world['CRS'] = self.data['metadata']['referenceSystem']
        
        new_objects = []
        cityobjs = {}

        progress_max = len(self.data['CityObjects'])
        progress = 0
        start_import = time.time()

        # Creating empty meshes for every CityObjects and linking its
        # geometries as children-meshes
        for objid, obj in self.data['CityObjects'].items():
            cityobject = create_empty_object(objid)
            cityobject = assign_properties(cityobject,
                                           obj)
            new_objects.append(cityobject)
            cityobjs[objid] = cityobject

            for i, geom in enumerate(obj['geometry']):
                geom_obj = self.parse_geometry(objid, obj, geom, i)
                geom_obj.parent = cityobject
                new_objects.append(geom_obj)

            progress += 1
            print("Importing: {percent}% completed"
                  .format(percent=round(progress * 100 / progress_max, 1)),
                  end="\r")
        end_import = time.time()

        progress = 0
        start_hier = time.time()

        #Assigning child building parts to parent buildings
        print ("\nBuilding hierarchy...")
        for objid, obj in self.data['CityObjects'].items():
            if 'parents' in obj:
                parent_id = obj['parents'][0]
                cityobjs[objid].parent = cityobjs[parent_id]

            progress += 1
            print("Building hierarchy: {percent}% completed"
                  .format(percent=round(progress * 100 / progress_max, 1)),
                  end="\r")
        end_hier = time.time()

        start_link = time.time()

        # Link everything to the scene
        print ("\nLinking objects to the scene...")
        collection = bpy.context.scene.collection
        for new_object in new_objects:
            if 'lod' in new_object:
                get_collection("LoD{}".format(new_object['lod'])).objects.link(new_object)
            else:
                collection.objects.link(new_object)


        end_link = time.time()

        #Console output
        # print("\n")
        print("\nCityJSON file successfully imported from '"+str(self.filepath)+"'.\n")
        print("Total importing time: ", round(end_import-start_import, 2), "s")
        print("Building hierarchy: ", round(end_hier-start_hier, 2), "s")
        print("Linking: ", round(end_link-start_link, 2), "s\n")

        return {'FINISHED'}
