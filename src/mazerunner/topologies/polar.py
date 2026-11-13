"""Polar (round / theta) topology. Cell = (ring, index). Outer rings subdivide; see docs/algorithms/topologies.md.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase ROUND_HEX). Constructor args: (rings,)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("polar", title="Polar (round / theta)", requires=(), phase=Phase.ROUND_HEX)
class PolarGrid(Topology):
    name = "polar"
    traits = frozenset({Trait.ROWS, Trait.PLANAR, Trait.HEADINGS, Trait.METRIC})

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("polar topology: phase ROUND_HEX")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
