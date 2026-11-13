"""Square (orthogonal) topology: the reference implementation of the Topology contract.

Cell = (row, col), row 0 at the top. Notes: docs/algorithms/topologies.md
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait

_DIRS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
_CCW = ("E", "N", "W", "S")  # counter-clockwise on screen


@topologies.register("square", title="Square (orthogonal)", phase=Phase.MVP, implemented=True)
class SquareGrid(Topology):
    name = "square"
    traits = frozenset({Trait.ROWS, Trait.ORTHOGONAL, Trait.RECTANGULAR, Trait.PLANAR,
                        Trait.HEADINGS, Trait.METRIC, Trait.UNIFORM_GRID})
    CELL = 1.0  # geometry units per cell

    def __init__(self, rows: int, cols: int | None = None) -> None:
        cols = rows if cols is None else cols
        if rows < 1 or cols < 1:
            raise ValueError("grid must be at least 1×1")
        self.R, self.C = rows, cols
        self.args = (rows, cols)
        self._nbrs: dict[Cell, tuple[Cell, ...]] = {}
        for r in range(rows):
            for c in range(cols):
                self._nbrs[(r, c)] = tuple(
                    n for d in _CCW if (n := self.axis_neighbor((r, c), d)) is not None)

    # --- core -----------------------------------------------------------
    def cells(self) -> Iterator[Cell]:
        for r in range(self.R):
            for c in range(self.C):
                yield (r, c)

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        return self._nbrs[cell]

    def __len__(self) -> int:
        return self.R * self.C

    def boundary(self) -> list[Cell]:
        R, C = self.R, self.C
        west_down = [(r, 0) for r in range(R // 2, R)]
        south = [(R - 1, c) for c in range(C)]
        east = [(r, C - 1) for r in range(R - 1, -1, -1)]
        north = [(0, c) for c in range(C - 1, -1, -1)]
        west_up = [(r, 0) for r in range(0, R // 2)]
        return west_down + south + east + north + west_up

    def position(self, cell: Cell) -> tuple[float, float]:
        r, c = cell
        return ((c + 0.5) * self.CELL, (r + 0.5) * self.CELL)

    def geometry(self) -> dict:
        s, idx = self.CELL, self.index
        cells = [[[c * s, r * s], [(c + 1) * s, r * s], [(c + 1) * s, (r + 1) * s], [c * s, (r + 1) * s]]
                 for r, c in self.cells()]
        walls = []
        for r, c in self.cells():
            i = idx[(r, c)]
            x0, y0, x1, y1 = c * s, r * s, (c + 1) * s, (r + 1) * s
            # east and south walls are shared; north/west only on the outer edge
            e, so = self.axis_neighbor((r, c), "E"), self.axis_neighbor((r, c), "S")
            walls.append({"a": i, "b": idx[e] if e else None, "pts": [[x1, y0], [x1, y1]]})
            walls.append({"a": i, "b": idx[so] if so else None, "pts": [[x0, y1], [x1, y1]]})
            if r == 0:
                walls.append({"a": i, "b": None, "pts": [[x0, y0], [x1, y0]]})
            if c == 0:
                walls.append({"a": i, "b": None, "pts": [[x0, y0], [x0, y1]]})
        return {"width": self.C * s, "height": self.R * s, "cells": cells, "walls": walls}

    # --- ROWS -----------------------------------------------------------
    def rows(self) -> Sequence[Sequence[Cell]]:
        return [[(r, c) for c in range(self.C)] for r in range(self.R)]

    def row_of(self, cell: Cell) -> int:
        return cell[0]

    def next_in_row(self, cell: Cell) -> Cell | None:
        return self.axis_neighbor(cell, "E")

    def prev_row_neighbors(self, cell: Cell) -> list[Cell]:
        n = self.axis_neighbor(cell, "N")
        return [n] if n else []

    def next_row_neighbors(self, cell: Cell) -> list[Cell]:
        s = self.axis_neighbor(cell, "S")
        return [s] if s else []

    # --- ORTHOGONAL -----------------------------------------------------
    def axis_neighbor(self, cell: Cell, direction: str) -> Cell | None:
        dr, dc = _DIRS[direction]
        r, c = cell[0] + dr, cell[1] + dc
        return (r, c) if 0 <= r < self.R and 0 <= c < self.C else None

    # --- HEADINGS / METRIC ---------------------------------------------
    def heading(self, src: Cell, dst: Cell) -> float:
        return math.atan2(src[0] - dst[0], dst[1] - src[1])

    def distance(self, a: Cell, b: Cell) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
