"""Hexagonal (sigma) topology. Cell = axial (q, r). distance = cube distance.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase ROUND_HEX). Constructor args: (rows, cols)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("hex", title="Hexagonal (sigma)", requires=(), phase=Phase.ROUND_HEX)
class HexGrid(Topology):
    name = "hex"
    traits = frozenset({Trait.ROWS, Trait.PLANAR, Trait.HEADINGS, Trait.METRIC})

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("hex topology: phase ROUND_HEX")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
