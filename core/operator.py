import bpy


class Up3dateCityJsonfy(bpy.types.Operator):
    bl_idname = "cityjson.cityjsonfy"
    bl_label = "Convert to cityjson"
    bl_context = "scene"

    def execute(self, context):
        scene = bpy.context.scene
        props = scene.cityjsonfy_properties

        # define properties
        lod_fullversion = props.lod
        if props.lod_version != 0:
            lod_fullversion = round(props.lod + (props.lod_version / 10), 1)

        # loop through selected objects
        for geom_obj in bpy.context.selected_objects:
            cityjson_id = geom_obj.name
            geom_location = geom_obj.location

            # create empty
            cityjson_object = bpy.data.objects.new("empty", None)
            scene.collection.objects.link(cityjson_object)
            cityjson_object.location = geom_location

            # set names and attributes
            geom_obj.name = f"{props.lod}: [LOD{lod_fullversion}] {cityjson_id}"
            geom_obj["type"] = props.geometry_type
            geom_obj["lod"] = props.lod
            cityjson_object.name = cityjson_id
            cityjson_object["type"] = props.feature_type

        return {"FINISHED"}
