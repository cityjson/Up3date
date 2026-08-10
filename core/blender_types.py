"""Structural types for the subset of Blender's Python API used by Up3date."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, MutableMapping, Sequence
from typing import Protocol, Self


class Vector(Protocol):
    """Vector-like value exposed by Blender's mesh API."""

    def __getitem__(self, index: int) -> float: ...

    def __iter__(self) -> Iterator[float]: ...


class Matrix(Protocol):
    """Matrix supporting Blender's matrix-vector multiplication."""

    def __matmul__(self, vector: Vector) -> Vector: ...


class CustomPropertyOwner(Protocol):
    def __setitem__(self, key: str, value: object) -> None: ...


class BlenderMaterial(CustomPropertyOwner, Protocol):
    name: str
    diffuse_color: tuple[float, float, float, float]

    def __getitem__(self, key: str) -> object: ...

    def __setitem__(self, key: str, value: object) -> None: ...

    def get(self, key: str, default: object = None) -> object: ...


class MaterialCollection(Protocol):
    def __bool__(self) -> bool: ...

    def __getitem__(self, index: int) -> BlenderMaterial | None: ...

    def __iter__(self) -> Iterator[BlenderMaterial | None]: ...

    def __len__(self) -> int: ...

    def append(self, material: BlenderMaterial) -> None: ...


class BlenderVertex(Protocol):
    co: Vector


class BlenderPolygon(Protocol):
    index: int
    material_index: int
    vertices: Sequence[int]


class VertexCollection(Protocol):
    def __getitem__(self, index: int) -> BlenderVertex: ...

    def __iter__(self) -> Iterator[BlenderVertex]: ...

    def __len__(self) -> int: ...

    def add(self, count: int) -> None: ...

    def foreach_set(self, attribute: str, values: Sequence[object]) -> None: ...


class PolygonCollection(Protocol):
    def __getitem__(self, index: int) -> BlenderPolygon: ...

    def __iter__(self) -> Iterator[BlenderPolygon]: ...

    def __len__(self) -> int: ...

    def add(self, count: int) -> None: ...

    def foreach_set(self, attribute: str, values: Sequence[object]) -> None: ...


class LoopCollection(Protocol):
    def add(self, count: int) -> None: ...

    def foreach_set(self, attribute: str, values: Sequence[object]) -> None: ...


class BlenderMesh(Protocol):
    materials: MaterialCollection
    vertices: VertexCollection
    polygons: PolygonCollection
    loops: LoopCollection

    def update(self) -> None: ...


class BlenderObject(CustomPropertyOwner, Protocol):
    name: str
    type: str
    data: BlenderMesh
    parent: BlenderObject | None
    location: Sequence[float]
    matrix_world: Matrix
    bound_box: Sequence[Sequence[float]]

    def __contains__(self, key: object) -> bool: ...

    def __getitem__(self, key: str) -> object: ...

    def __setitem__(self, key: str, value: object) -> None: ...

    def get(self, key: str, default: object = None) -> object: ...

    def items(self) -> Iterable[tuple[str, object]]: ...


class ObjectLinker(Protocol):
    def link(self, obj: BlenderObject) -> None: ...


class CollectionLinker(Protocol):
    def link(self, collection: BlenderCollection) -> None: ...


class BlenderCollection(Protocol):
    objects: ObjectLinker
    children: CollectionLinker


class Up3dateProperties(Protocol):
    lod: str
    feature_type: str
    geometry_type: str


class BlenderScene(Protocol):
    world: MutableMapping[str, object]
    collection: BlenderCollection
    cityjsonfy_properties: Up3dateProperties


class BlenderContext(Protocol):
    scene: BlenderScene
    selected_objects: Iterable[BlenderObject]


class UILayout(Protocol):
    def label(self, *, text: str) -> None: ...

    def operator(self, operator: str, *, text: str = "") -> object: ...

    def prop(self, data: object, property: str) -> None: ...

    def row(self, *, align: bool = False) -> Self: ...


class Menu(Protocol):
    layout: UILayout
