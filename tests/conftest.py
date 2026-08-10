"""Shared fixtures for CityJSON 2.0.2 tests."""

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

# Core modules import Blender's Python API.  A small module stub lets unit tests
# exercise their pure logic without starting Blender (which is covered by
# integration testing rather than this unit-test suite).
PROJECT_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_PARENT))

bpy = ModuleType("bpy")
bpy.context = SimpleNamespace()
bpy.data = SimpleNamespace()
sys.modules["bpy"] = bpy


class IDPropertyArray(list):
    def to_list(self):
        return list(self)


idprop = ModuleType("idprop")
idprop.types = SimpleNamespace(IDPropertyArray=IDPropertyArray)
sys.modules["idprop"] = idprop

MINIMAL_CITYJSON = {
    "type": "CityJSON",
    "version": "2.0",
    "transform": {
        "scale": [0.001, 0.001, 0.001],
        "translate": [84710.0, 446846.0, -5.3],
    },
    "metadata": {
        "referenceSystem": "https://www.opengis.net/def/crs/EPSG/0/7415",
        "geographicalExtent": [84710.1, 446846.0, -5.3, 84820.0, 446940.0, 40.2],
    },
    "CityObjects": {
        "building-1": {
            "type": "Building",
            "attributes": {"measuredHeight": 10.5, "roofType": "Flat"},
            "children": ["building-1-part"],
            "geometry": [
                {
                    "type": "MultiSurface",
                    "lod": "1",
                    "boundaries": [
                        [[[0, 1, 2, 3]]],
                        [[[4, 5, 6, 7]]],
                    ],
                    "semantics": {
                        "surfaces": [
                            {"type": "WallSurface"},
                            {"type": "RoofSurface"},
                        ],
                        "values": [0, 1],
                    },
                }
            ],
        },
        "building-1-part": {
            "type": "BuildingPart",
            "parents": ["building-1"],
            "geometry": [],
        },
    },
    "vertices": [
        [0, 0, 0],
        [1000, 0, 0],
        [1000, 1000, 0],
        [0, 1000, 0],
        [0, 0, 10000],
        [1000, 0, 10000],
        [1000, 1000, 10000],
        [0, 1000, 10000],
    ],
}


CITYJSON_WITH_SOLID = {
    "type": "CityJSON",
    "version": "2.0",
    "CityObjects": {
        "tunnel-1": {
            "type": "Tunnel",
            "geometry": [
                {
                    "type": "Solid",
                    "lod": "2",
                    "boundaries": [
                        [
                            [[[0, 1, 2, 3]]],
                            [[[4, 5, 6, 7]]],
                        ]
                    ],
                }
            ],
        }
    },
    "vertices": [
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 1],
        [1, 1, 1],
        [0, 1, 1],
    ],
}


CITYJSON_WITH_APPEARANCE = {
    "type": "CityJSON",
    "version": "2.0",
    "CityObjects": {},
    "vertices": [],
    "appearance": {
        "materials": [{"name": "mat1", "ambientIntensity": 0.2}],
        "textures": [{"type": "PNG", "image": "facade.png"}],
        "vertices-texture": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]],
        "default-theme-texture": "myTheme",
        "default-theme-material": "myMatTheme",
    },
}


CITYJSON_WITH_TEMPLATES = {
    "type": "CityJSON",
    "version": "2.0",
    "CityObjects": {
        "tree-1": {
            "type": "SolitaryVegetationObject",
            "geometry": [
                {
                    "type": "GeometryInstance",
                    "template": 0,
                    "boundaries": [2],
                    "transformationMatrix": [
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                    ],
                }
            ],
        }
    },
    "vertices": [[0, 0, 0], [1, 0, 0], [10, 20, 0]],
    "geometry-templates": {
        "templates": [
            {
                "type": "MultiSurface",
                "lod": "1",
                "boundaries": [[[[0, 1, 2]]]],
            }
        ],
        "vertices-templates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0]],
    },
}


@pytest.fixture
def minimal_dict():
    return MINIMAL_CITYJSON


@pytest.fixture
def solid_dict():
    return CITYJSON_WITH_SOLID


@pytest.fixture
def appearance_dict():
    return CITYJSON_WITH_APPEARANCE


@pytest.fixture
def templates_dict():
    return CITYJSON_WITH_TEMPLATES
