import bpy


class Up3dateCityJSONfyProperties(bpy.types.PropertyGroup):
    lod: bpy.props.StringProperty(name="LOD", default="2")
    feature_type: bpy.props.StringProperty(
        name="feature_type",
        default="Building",
    )
    geometry_type: bpy.props.EnumProperty(
        name="geometry_type",
        description="",
        items=[
            ("MultiSurface", "MultiSurface", "MultiSurface"),
            ("CompositeSurface", "CompositeSurface", "CompositeSurface"),
            ("Solid", "Solid", "Solid"),
            ("MultiSolid", "MultiSolid", "MultiSolid"),
        ],
    )
