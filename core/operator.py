import bpy


class Up3dateCityJsonfy(bpy.types.Operator):
    bl_idname = "cityjson.cityjsonfy"
    bl_label = "Convert to cityjson"
    bl_context = "scene"

    def execute(self, context):
        scene = context.scene
        props = scene.cityjsonfy_properties

        # loop through selected objects
        for geom_obj in context.selected_objects:
            cityjson_id = geom_obj.name
            geom_location = geom_obj.location

            # create empty
            cityjson_object = bpy.data.objects.new("empty", None)
            scene.collection.objects.link(cityjson_object)
            cityjson_object.location = geom_location

            # set names and attributes
            geom_obj.name = f"{props.lod}: [LOD{props.lod}] {cityjson_id}"
            geom_obj["type"] = props.geometry_type
            geom_obj["lod"] = props.lod
            cityjson_object.name = cityjson_id
            cityjson_object["type"] = props.feature_type

        return {"FINISHED"}
