"""Weave (over/under square) topology. Square grid with under-passage cells; Buck ch.9. Not PLANAR.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase PLACEHOLDER). Constructor args: (rows, cols)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("weave", title="Weave (over/under square)", requires=(), phase=Phase.PLACEHOLDER)
class WeaveGrid(Topology):
    name = "weave"
    traits = frozenset({Trait.ROWS, Trait.ORTHOGONAL, Trait.HEADINGS, Trait.METRIC, Trait.WEAVE})

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("weave topology: phase PLACEHOLDER")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
