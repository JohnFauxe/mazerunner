"""Triangle (delta) topology. Alternating up/down triangles, degree ≤3.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase PLACEHOLDER). Constructor args: (rows, cols)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("triangle", title="Triangle (delta)", requires=(), phase=Phase.PLACEHOLDER)
class TriangleGrid(Topology):
    name = "triangle"
    traits = frozenset({Trait.ROWS, Trait.PLANAR, Trait.HEADINGS, Trait.METRIC})

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("triangle topology: phase PLACEHOLDER")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
