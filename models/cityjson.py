from typing import Any, TypedDict


class CityJSON(TypedDict):
    type: str
    version: str
    metadata: dict[str, Any]
    CityObjects: dict[str, dict[str, Any]]
    vertices: list[list[float]]
