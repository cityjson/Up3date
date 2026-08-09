"""
Python dataclass for CityJSON 2.0.2 geometry templates.

Generated from:
    https://3d.bk.tudelft.nl/schemas/cityjson/2.0.2/geomtemplates.schema.json
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class GeometryInstance:
    """schema: GeometryInstance.

    Places an instance of a geometry template (referenced by index into the
    CityJSON `geometry-templates.templates` array) at a given vertex, with
    a 4x4 transformation matrix (16 numbers, row-major) applied to it.
    """

    template: int
    # exactly one vertex index -- the anchor point the template is placed at
    boundaries: list[int] = field(default_factory=list)  # len == 1
    # 4x4 transformation matrix, flattened row-major, exactly 16 numbers
    transformationMatrix: list[float] = field(default_factory=list)  # len == 16
    type: Literal["GeometryInstance"] = "GeometryInstance"
