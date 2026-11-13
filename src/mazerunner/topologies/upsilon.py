"""Upsilon (octagon + square) topology. Mixed degree 8/4.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase PLACEHOLDER). Constructor args: (rows, cols)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("upsilon", title="Upsilon (octagon + square)", requires=(), phase=Phase.PLACEHOLDER)
class UpsilonGrid(Topology):
    name = "upsilon"
    traits = frozenset({Trait.ROWS, Trait.PLANAR, Trait.METRIC})

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("upsilon topology: phase PLACEHOLDER")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
