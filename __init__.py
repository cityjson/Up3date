"""Entry point for the Up3date Blender add-on."""

bl_info = {
    "name": "Up3date",
    "author": "Konstantinos Mastorakis",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "File > Import > CityJSON (.json) || File > Export > CityJSON (.json)",
    "description": "Visualize, edit and export 3D City Models encoded in CityJSON format",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}


def register() -> None:
    """Load and register the Blender-dependent add-on implementation."""
    from . import addon

    addon.register()


def unregister() -> None:
    """Unregister the Blender-dependent add-on implementation."""
    from . import addon

    addon.unregister()
