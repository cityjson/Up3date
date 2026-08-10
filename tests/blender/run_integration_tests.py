"""Run Up3date integration tests inside Blender's background process."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import bpy

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT.parent))

coverage_session = None
if coverage_file := os.environ.get("COVERAGE_FILE"):
    import coverage

    coverage_session = coverage.Coverage(
        branch=True,
        data_file=coverage_file,
        omit=[str(PROJECT_ROOT / ".venv" / "*"), str(PROJECT_ROOT / "tests" / "*")],
        source=[str(PROJECT_ROOT)],
    )
    coverage_session.start()

import Up3date
from Up3date import addon
from Up3date.core.objects import CityJSONExporter, CityJSONParser
from Up3date.core.utils import create_mesh_object, get_collection, remove_scene_objects
from Up3date.models.cityjson import CityJSONDocument


class BlenderIntegrationTests(unittest.TestCase):
    """Exercise Blender data blocks, registration, and CityJSON round trips."""

    def setUp(self) -> None:
        remove_scene_objects()
        self._addon_registered = False

    def tearDown(self) -> None:
        if self._addon_registered:
            addon.unregister()
        remove_scene_objects()

    def test_create_mesh_object_and_collection(self) -> None:
        material = bpy.data.materials.new("WallSurface")
        mesh_object = create_mesh_object(
            "triangle",
            [(0, 0, 0), (1, 0, 0), (0, 1, 0)],
            [(0, 1, 2)],
            [material],
            [0],
        )
        collection = get_collection("LoD1")
        collection.objects.link(mesh_object)

        self.assertEqual(len(mesh_object.data.vertices), 3)
        self.assertEqual(len(mesh_object.data.polygons), 1)
        self.assertEqual(tuple(mesh_object.data.polygons[0].vertices), (0, 1, 2))
        self.assertIs(mesh_object.data.materials[0], material)
        self.assertIn(mesh_object, collection.objects.values())

    def test_addon_registration_and_operator(self) -> None:
        Up3date.register()
        self._addon_registered = True
        self.assertTrue(hasattr(bpy.types.Scene, "cityjsonfy_properties"))

        menu_calls = []
        menu = SimpleNamespace(
            layout=SimpleNamespace(
                operator=lambda operator, **kwargs: menu_calls.append(
                    (operator, kwargs)
                )
            )
        )
        addon.menu_func_import(menu, bpy.context)
        addon.menu_func_export(menu, bpy.context)
        self.assertEqual(
            menu_calls,
            [
                ("cityjson.import_file", {"text": "CityJSON (.json)"}),
                ("cityjson.export_file", {"text": "CityJSON (.json)"}),
            ],
        )

        mesh = bpy.data.meshes.new("source-mesh")
        source = bpy.data.objects.new("building-1", mesh)
        bpy.context.scene.collection.objects.link(source)
        source.select_set(True)
        bpy.context.view_layer.objects.active = source
        props = bpy.context.scene.cityjsonfy_properties
        props.lod = "2"
        props.feature_type = "Building"
        props.geometry_type = "MultiSurface"

        result = bpy.ops.cityjson.cityjsonfy()

        self.assertEqual(result, {"FINISHED"})
        self.assertEqual(source.name, "2: [LOD2] building-1")
        self.assertEqual(source["type"], "MultiSurface")
        self.assertEqual(source["lod"], "2")
        parent = bpy.data.objects["building-1"]
        self.assertEqual(parent.type, "EMPTY")
        self.assertEqual(parent["type"], "Building")

        Up3date.unregister()
        self._addon_registered = False
        self.assertFalse(hasattr(bpy.types.Scene, "cityjsonfy_properties"))

    def test_import_then_export_cityjson(self) -> None:
        cityjson = {
            "type": "CityJSON",
            "version": "2.0",
            "CityObjects": {
                "building-1": {
                    "type": "Building",
                    "attributes": {"height": 12},
                    "geometry": [
                        {
                            "type": "MultiSurface",
                            "lod": "1",
                            "boundaries": [[[0, 1, 2]]],
                        }
                    ],
                }
            },
            "vertices": [[10, 20, 0], [11, 20, 0], [10, 21, 0]],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.city.json"
            output_path = Path(temp_dir) / "output.city.json"
            input_path.write_text(json.dumps(cityjson), encoding="utf-8")

            import_result = addon.ImportCityJSON.execute(
                SimpleNamespace(
                    filepath=str(input_path),
                    material_type="SURFACES",
                    reuse_materials=False,
                    clean_scene=True,
                ),
                bpy.context,
            )

            self.assertEqual(import_result, {"FINISHED"})
            parent = bpy.data.objects["building-1"]
            geometry = bpy.data.objects["0: [LoD1] building-1"]
            self.assertEqual(parent["type"], "Building")
            self.assertEqual(parent["attributes.height"], 12)
            self.assertIs(geometry.parent, parent)
            self.assertEqual(len(geometry.data.polygons), 1)

            export_result = addon.ExportCityJSON.execute(
                SimpleNamespace(
                    filepath=str(output_path),
                    check_for_duplicates=True,
                    precision=3,
                ),
                bpy.context,
            )
            exported = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(export_result, {"FINISHED"})
        self.assertEqual(exported["CityObjects"]["building-1"]["type"], "Building")
        self.assertEqual(
            exported["CityObjects"]["building-1"]["attributes"]["height"], 12
        )
        self.assertEqual(
            exported["CityObjects"]["building-1"]["geometry"][0]["type"],
            "MultiSurface",
        )
        self.assertEqual(len(exported["vertices"]), 3)

    def test_real_datasets_round_trip(self) -> None:
        data_dir = PROJECT_ROOT / "tests" / "data"

        for input_path in sorted(data_dir.glob("*.city.json")):
            with self.subTest(dataset=input_path.name):
                print(f"Round-tripping real dataset: {input_path.name}", flush=True)
                remove_scene_objects()
                source = json.loads(input_path.read_text(encoding="utf-8"))
                source_geometry_count = sum(
                    len(city_object.get("geometry", []))
                    for city_object in source["CityObjects"].values()
                )

                import_result = CityJSONParser(
                    str(input_path),
                    material_type="SURFACES",
                    reuse_materials=True,
                    clear_scene=True,
                ).execute()

                self.assertEqual(import_result, {"FINISHED"})
                imported_city_object_ids = {
                    obj.get("cityjson_id", obj.name)
                    for obj in bpy.data.objects
                    if obj.get("cityjson_id", obj.name) in source["CityObjects"]
                }
                self.assertEqual(imported_city_object_ids, set(source["CityObjects"]))

                with tempfile.TemporaryDirectory() as temp_dir:
                    output_path = Path(temp_dir) / input_path.name
                    export_result = CityJSONExporter(
                        str(output_path), check_for_duplicates=True, precision=3
                    ).execute()
                    exported = json.loads(output_path.read_text(encoding="utf-8"))

                exported_geometry_count = sum(
                    len(city_object.get("geometry", []))
                    for city_object in exported["CityObjects"].values()
                )
                self.assertEqual(export_result, {"FINISHED"})
                self.assertEqual(
                    set(exported["CityObjects"]), set(source["CityObjects"])
                )
                self.assertEqual(exported_geometry_count, source_geometry_count)
                if "transform" in source:
                    self.assertEqual(exported["transform"], source["transform"])
                for key in ("extensions", "appearance", "geometry-templates"):
                    if source.get(key):
                        self.assertEqual(exported[key], source[key])
                CityJSONDocument.from_dict(exported)

    def test_transformed_solid_with_semantics_round_trip(self) -> None:
        cityjson = {
            "type": "CityJSON",
            "version": "2.0",
            "transform": {
                "scale": [0.1, 0.1, 0.1],
                "translate": [100.0, 200.0, 5.0],
            },
            "CityObjects": {
                "building-1": {
                    "type": "Building",
                    "geometry": [
                        {
                            "type": "Solid",
                            "lod": "2",
                            "boundaries": [[[[0, 1, 2, 3]]]],
                            "semantics": {
                                "surfaces": [{"type": "RoofSurface"}],
                                "values": [[0]],
                            },
                        }
                    ],
                }
            },
            "vertices": [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "solid.city.json"
            output_path = Path(temp_dir) / "solid-output.city.json"
            input_path.write_text(json.dumps(cityjson), encoding="utf-8")

            CityJSONParser(
                str(input_path),
                material_type="SURFACES",
                reuse_materials=False,
                clear_scene=True,
            ).execute()
            CityJSONExporter(
                str(output_path), check_for_duplicates=True, precision=3
            ).execute()
            exported = json.loads(output_path.read_text(encoding="utf-8"))

        geometry = exported["CityObjects"]["building-1"]["geometry"][0]
        self.assertEqual(exported["transform"], cityjson["transform"])
        self.assertEqual(exported["vertices"], cityjson["vertices"])
        self.assertEqual(geometry["type"], "Solid")
        self.assertEqual(geometry["semantics"]["surfaces"], [{"type": "RoofSurface"}])
        self.assertEqual(geometry["semantics"]["values"], [[0]])


suite = unittest.defaultTestLoader.loadTestsFromTestCase(BlenderIntegrationTests)
result = unittest.TextTestRunner(verbosity=2).run(suite)

if coverage_session is not None:
    coverage_session.stop()
    coverage_session.save()

if not result.wasSuccessful():
    raise RuntimeError("Blender integration tests failed")
