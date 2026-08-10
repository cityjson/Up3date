"""Validation tests for the real CityJSON samples kept in the repository."""

import json
from pathlib import Path

import pytest

from models.cityjson import CityJSONDocument

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    ("filename", "city_object_count", "vertex_count"),
    [
        ("3dbag.city.json", 2_221, 82_509),
        ("noise_data.city.json", 5, 16),
        ("LoD3_Railway.city.json", 121, 73_554),
        ("Vienna_102081.city.json", 1_322, 47_220),
    ],
)
def test_sample_dataset_deserializes(filename, city_object_count, vertex_count):
    raw = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))

    document = CityJSONDocument.from_dict(raw)

    assert document.type == "CityJSON"
    assert document.version == "2.0"
    assert len(document.city_objects) == city_object_count
    assert len(document.vertices) == vertex_count
