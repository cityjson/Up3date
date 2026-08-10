import bpy

from .blender_types import BlenderContext


class Up3datePTgui(bpy.types.Panel):
    """Creates a Panel in the scene context of properties editor"""

    bl_idname = "CITYJSON_PT_gui"
    bl_label = "Up3date"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context: BlenderContext) -> None:
        layout = self.layout

        scene = context.scene
        props = scene.cityjsonfy_properties

        layout.label(text="Convert selected to CityJSON:")
        row = layout.row(align=True)
        row.prop(props, "lod")
        row = layout.row()
        row.prop(props, "feature_type")
        row = layout.row()
        row.prop(props, "geometry_type")
        row = layout.row()
        row.operator("cityjson.cityjsonfy")
