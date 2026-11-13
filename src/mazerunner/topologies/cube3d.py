"""3D / multi-level topology. Stacked square grids with up/down links; Buck ch.13.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase PLACEHOLDER). Constructor args: (levels, rows, cols)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("3d", title="3D / multi-level", requires=(), phase=Phase.PLACEHOLDER)
class LayeredGrid(Topology):
    name = "3d"
    traits = frozenset({Trait.ROWS, Trait.METRIC})

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("3d topology: phase PLACEHOLDER")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
