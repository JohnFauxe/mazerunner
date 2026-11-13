"""Masked / arbitrary shape topology. Square grid restricted by an image/text mask; traits depend on mask.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase PLACEHOLDER). Constructor args: (mask,)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("masked", title="Masked / arbitrary shape", requires=(), phase=Phase.PLACEHOLDER)
class MaskedGrid(Topology):
    name = "masked"
    traits = frozenset()

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("masked topology: phase PLACEHOLDER")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
