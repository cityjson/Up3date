"""Tests for models/cityjson.py — CityJSON 2.0.2 root document and supporting types."""

import pytest

from models.cityjson import (
    Appearance,
    CityJSON,
    CityJSONDocument,
    GeometryTemplates,
    Metadata,
    Transform,
)
from models.cityobjects import Building
from models.geomprimitives import MultiSurface


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

class TestTransform:
    def test_from_dict(self):
        t = Transform.from_dict({"scale": [0.001, 0.001, 0.001], "translate": [1.0, 2.0, 3.0]})
        assert t.scale == [0.001, 0.001, 0.001]
        assert t.translate == [1.0, 2.0, 3.0]

    def test_to_dict(self):
        t = Transform(scale=[0.001, 0.001, 0.001], translate=[84710.0, 446846.0, -5.3])
        d = t.to_dict()
        assert d["scale"] == [0.001, 0.001, 0.001]
        assert d["translate"] == [84710.0, 446846.0, -5.3]

    def test_roundtrip(self):
        raw = {"scale": [0.001, 0.001, 0.001], "translate": [100.0, 200.0, 0.0]}
        assert Transform.from_dict(raw).to_dict() == raw

    def test_scale_length_three(self):
        t = Transform.from_dict({"scale": [1.0, 2.0, 3.0], "translate": [0.0, 0.0, 0.0]})
        assert len(t.scale) == 3
        assert len(t.translate) == 3


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class TestMetadata:
    def test_empty(self):
        m = Metadata()
        assert m.geographicalExtent is None
        assert m.identifier is None
        assert m.pointOfContact is None
        assert m.referenceDate is None
        assert m.referenceSystem is None
        assert m.title is None
        assert m.extra == {}

    def test_from_dict_basic(self):
        raw = {
            "referenceSystem": "https://www.opengis.net/def/crs/EPSG/0/7415",
            "geographicalExtent": [0.0, 0.0, 0.0, 1.0, 1.0, 10.0],
        }
        m = Metadata.from_dict(raw)
        assert m.referenceSystem == "https://www.opengis.net/def/crs/EPSG/0/7415"
        assert m.geographicalExtent == [0.0, 0.0, 0.0, 1.0, 1.0, 10.0]

    def test_from_dict_point_of_contact(self):
        raw = {"pointOfContact": {"contactName": "Jane", "emailAddress": "jane@example.com"}}
        m = Metadata.from_dict(raw)
        assert m.pointOfContact == {"contactName": "Jane", "emailAddress": "jane@example.com"}

    def test_from_dict_all_named_fields(self):
        raw = {
            "identifier": "abc-123",
            "referenceDate": "2024-01-01",
            "title": "Test Dataset",
        }
        m = Metadata.from_dict(raw)
        assert m.identifier == "abc-123"
        assert m.referenceDate == "2024-01-01"
        assert m.title == "Test Dataset"
        assert m.extra == {}

    def test_from_dict_extra_fields_captured(self):
        raw = {"someCustomProp": "My City", "anotherCustom": "value"}
        m = Metadata.from_dict(raw)
        assert m.extra["someCustomProp"] == "My City"
        assert m.extra["anotherCustom"] == "value"

    def test_to_dict_omits_none(self):
        m = Metadata()
        d = m.to_dict()
        assert "geographicalExtent" not in d
        assert "referenceSystem" not in d
        assert "pointOfContact" not in d

    def test_to_dict_includes_named_fields(self):
        m = Metadata(title="Test", identifier="id-1", referenceDate="2024-01-01")
        d = m.to_dict()
        assert d["title"] == "Test"
        assert d["identifier"] == "id-1"
        assert d["referenceDate"] == "2024-01-01"

    def test_to_dict_includes_extra(self):
        m = Metadata.from_dict({"someCustom": "value"})
        d = m.to_dict()
        assert d["someCustom"] == "value"

    def test_roundtrip(self):
        raw = {
            "referenceSystem": "https://www.opengis.net/def/crs/EPSG/0/4979",
            "geographicalExtent": [0.0, 0.0, 0.0, 10.0, 10.0, 50.0],
            "identifier": "abc-123",
            "referenceDate": "2024-01-01",
            "title": "My Dataset",
        }
        result = Metadata.from_dict(raw).to_dict()
        assert result == raw


# ---------------------------------------------------------------------------
# Appearance
# ---------------------------------------------------------------------------

class TestAppearance:
    def test_defaults(self):
        a = Appearance()
        assert a.materials == []
        assert a.textures == []
        assert a.vertices_texture == []
        assert a.default_theme_texture is None
        assert a.default_theme_material is None

    def test_from_dict_hyphenated_keys(self):
        raw = {
            "materials": [{"name": "mat1"}],
            "textures": [{"type": "PNG", "image": "img.png"}],
            "vertices-texture": [[0.0, 0.0], [1.0, 1.0]],
            "default-theme-texture": "myTexTheme",
            "default-theme-material": "myMatTheme",
        }
        a = Appearance.from_dict(raw)
        assert len(a.materials) == 1
        assert len(a.textures) == 1
        assert a.vertices_texture == [[0.0, 0.0], [1.0, 1.0]]
        assert a.default_theme_texture == "myTexTheme"
        assert a.default_theme_material == "myMatTheme"

    def test_to_dict_uses_hyphenated_keys(self):
        a = Appearance(
            vertices_texture=[[0.0, 0.0]],
            default_theme_texture="theme1",
            default_theme_material="theme2",
        )
        d = a.to_dict()
        assert "vertices-texture" in d
        assert "default-theme-texture" in d
        assert "default-theme-material" in d
        assert "vertices_texture" not in d

    def test_to_dict_omits_empty(self):
        d = Appearance().to_dict()
        assert d == {}

    def test_roundtrip(self):
        raw = {
            "materials": [{"name": "m1"}],
            "vertices-texture": [[0.0, 1.0]],
            "default-theme-texture": "t1",
        }
        result = Appearance.from_dict(raw).to_dict()
        assert result == raw


# ---------------------------------------------------------------------------
# GeometryTemplates
# ---------------------------------------------------------------------------

class TestGeometryTemplates:
    def test_defaults(self):
        gt = GeometryTemplates()
        assert gt.templates == []
        assert gt.vertices_templates == []

    def test_from_dict(self):
        raw = {
            "templates": [
                {"type": "MultiSurface", "lod": "1", "boundaries": [[[[0, 1, 2]]]]}
            ],
            "vertices-templates": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
        }
        gt = GeometryTemplates.from_dict(raw)
        assert len(gt.templates) == 1
        assert isinstance(gt.templates[0], MultiSurface)
        assert gt.vertices_templates == [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]

    def test_to_dict_uses_hyphenated_key(self):
        gt = GeometryTemplates(vertices_templates=[[0.0, 0.0, 0.0]])
        d = gt.to_dict()
        assert "vertices-templates" in d
        assert "vertices_templates" not in d

    def test_to_dict_omits_empty(self):
        d = GeometryTemplates().to_dict()
        assert d == {}

    def test_roundtrip(self):
        raw = {
            "templates": [{"type": "MultiSurface", "lod": "1", "boundaries": [[[[0, 1, 2]]]]}],
            "vertices-templates": [[0.0, 0.0, 0.0]],
        }
        result = GeometryTemplates.from_dict(raw).to_dict()
        assert result == raw


# ---------------------------------------------------------------------------
# CityJSONDocument
# ---------------------------------------------------------------------------

class TestCityJSONDocument:
    def test_defaults(self):
        doc = CityJSONDocument()
        assert doc.type == "CityJSON"
        assert doc.version == "2.0"
        assert doc.CityObjects == {}
        assert doc.vertices == []
        assert doc.transform is None
        assert doc.metadata is None
        assert doc.appearance is None
        assert doc.geometry_templates is None
        assert doc.extensions == {}

    def test_version_is_2_0(self):
        doc = CityJSONDocument()
        assert doc.version == "2.0"

    def test_cityjson_alias(self):
        assert CityJSON is CityJSONDocument

    def test_from_dict_minimal(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        assert doc.type == "CityJSON"
        assert doc.version == "2.0"
        assert len(doc.CityObjects) == 2
        assert len(doc.vertices) == 8

    def test_from_dict_transform(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        assert doc.transform is not None
        assert doc.transform.scale == [0.001, 0.001, 0.001]
        assert doc.transform.translate[0] == pytest.approx(84710.0)

    def test_from_dict_metadata(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        assert doc.metadata is not None
        assert "EPSG" in doc.metadata.referenceSystem

    def test_from_dict_cityobjects_typed(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        assert isinstance(doc.CityObjects["building-1"], Building)

    def test_from_dict_no_transform(self):
        raw = {"type": "CityJSON", "version": "2.0", "CityObjects": {}, "vertices": []}
        doc = CityJSONDocument.from_dict(raw)
        assert doc.transform is None

    def test_from_dict_geometry_templates(self, templates_dict):
        doc = CityJSONDocument.from_dict(templates_dict)
        assert doc.geometry_templates is not None
        assert len(doc.geometry_templates.templates) == 1
        assert doc.geometry_templates.vertices_templates == [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.5, 1.0, 0.0]]

    def test_from_dict_appearance(self, appearance_dict):
        doc = CityJSONDocument.from_dict(appearance_dict)
        assert doc.appearance is not None
        assert doc.appearance.default_theme_texture == "myTheme"

    def test_to_dict_version_is_2_0(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        d = doc.to_dict()
        assert d["version"] == "2.0"

    def test_to_dict_geometry_templates_key(self, templates_dict):
        doc = CityJSONDocument.from_dict(templates_dict)
        d = doc.to_dict()
        assert "geometry-templates" in d
        assert "geometry_templates" not in d

    def test_to_dict_omits_none_fields(self):
        doc = CityJSONDocument()
        d = doc.to_dict()
        assert "transform" not in d
        assert "metadata" not in d
        assert "appearance" not in d
        assert "geometry-templates" not in d
        assert "extensions" not in d

    def test_to_dict_includes_extensions_when_set(self):
        doc = CityJSONDocument(extensions={"myExt": {"url": "https://example.com", "version": "1.0"}})
        d = doc.to_dict()
        assert "extensions" in d

    def test_full_roundtrip(self, minimal_dict):
        doc = CityJSONDocument.from_dict(minimal_dict)
        result = doc.to_dict()
        assert result["type"] == "CityJSON"
        assert result["version"] == "2.0"
        assert "building-1" in result["CityObjects"]
        assert result["CityObjects"]["building-1"]["type"] == "Building"
        assert result["transform"]["scale"] == [0.001, 0.001, 0.001]
