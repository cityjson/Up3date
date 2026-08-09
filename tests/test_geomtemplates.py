"""Tests for models/geomtemplates.py — GeometryInstance."""

from models.geomtemplates import GeometryInstance


class TestGeometryInstance:
    def test_type_literal(self):
        gi = GeometryInstance(template=0)
        assert gi.type == "GeometryInstance"

    def test_defaults(self):
        gi = GeometryInstance(template=0)
        assert gi.boundaries == []
        assert gi.transformationMatrix == []

    def test_from_dict(self):
        matrix = [
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ]
        raw = {
            "type": "GeometryInstance",
            "template": 2,
            "boundaries": [5],
            "transformationMatrix": matrix,
        }
        gi = GeometryInstance.from_dict(raw)
        assert gi.template == 2
        assert gi.boundaries == [5]
        assert len(gi.transformationMatrix) == 16
        assert gi.transformationMatrix[0] == 1.0

    def test_boundaries_length_one(self):
        gi = GeometryInstance.from_dict({
            "type": "GeometryInstance",
            "template": 0,
            "boundaries": [3],
            "transformationMatrix": [1.0] * 16,
        })
        assert len(gi.boundaries) == 1

    def test_transformation_matrix_length_16(self):
        gi = GeometryInstance.from_dict({
            "type": "GeometryInstance",
            "template": 0,
            "boundaries": [0],
            "transformationMatrix": [float(i) for i in range(16)],
        })
        assert len(gi.transformationMatrix) == 16

    def test_to_dict_roundtrip(self):
        matrix = [1.0, 0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0, 0.0,
                  0.0, 0.0, 1.0, 0.0,
                  0.0, 0.0, 0.0, 1.0]
        raw = {
            "type": "GeometryInstance",
            "template": 0,
            "boundaries": [1],
            "transformationMatrix": matrix,
        }
        assert GeometryInstance.from_dict(raw).to_dict() == raw
