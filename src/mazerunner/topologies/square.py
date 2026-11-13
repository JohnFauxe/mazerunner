"""Square (orthogonal) topology. Cell = (row, col). distance = Manhattan.

Notes: docs/algorithms/topologies.md
Status: placeholder (phase MVP). Constructor args: (rows, cols)
"""
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait


@topologies.register("square", title="Square (orthogonal)", requires=(), phase=Phase.MVP)
class SquareGrid(Topology):
    name = "square"
    traits = frozenset({Trait.ROWS, Trait.ORTHOGONAL, Trait.RECTANGULAR, Trait.PLANAR, Trait.HEADINGS, Trait.METRIC, Trait.UNIFORM_GRID})

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("square topology: phase MVP")

    def cells(self) -> Iterator[Cell]:
        raise NotImplementedError

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
