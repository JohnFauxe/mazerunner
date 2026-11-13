"""Hexagonal (sigma) topology on a rectangular "odd-q" offset layout.

Notes: docs/algorithms/topologies.md. Constructor args: (rows, cols)

Cell = (row, col) offset coordinates (row 0 at the top). Hexes are *flat-topped* (Buck ch.8 /
redblobgames "odd-q"): odd columns are shoved down by half a hex. Unit hex size s=1 (corner
radius), so a hex is 2 wide and sqrt(3) tall, columns are 1.5 apart.

neighbors() are CCW on screen in direction order UR(30deg), U, UL, LL, D, LR (missing ones skipped);
geometry edge j faces the same direction. distance is the cube distance (admissible, and exact
on the open rectangle). ROWS hooks: prev/next_row_neighbors are the neighbours in row-1/row+1,
which are 1 (odd column up / even column down) or 3 cells, because the layout is staggered;
next_in_row = (row, col+1), which is always a neighbour.
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait

_S3 = math.sqrt(3.0)


@topologies.register("hex", title="Hexagonal (sigma)", requires=(), phase=Phase.ROUND_HEX,
                     implemented=True)
class HexGrid(Topology):
    name = "hex"
    traits = frozenset({Trait.ROWS, Trait.PLANAR, Trait.HEADINGS, Trait.METRIC})

    def __init__(self, rows: int, cols: int | None = None) -> None:
        cols = rows if cols is None else cols
        if rows < 1 or cols < 1:
            raise ValueError("grid must be at least 1×1")
        self.R, self.C = rows, cols
        self.args = (rows, cols)
        self._dirs: dict[Cell, tuple[Cell | None, ...]] = {}
        self._nbrs: dict[Cell, tuple[Cell, ...]] = {}
        for r in range(rows):
            for c in range(cols):
                d = c & 1
                cand = ((r - 1 + d, c + 1), (r - 1, c), (r - 1 + d, c - 1),
                        (r + d, c - 1), (r + 1, c), (r + d, c + 1))
                full = tuple(n if 0 <= n[0] < rows and 0 <= n[1] < cols else None for n in cand)
                self._dirs[(r, c)] = full
                self._nbrs[(r, c)] = tuple(n for n in full if n is not None)

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
        return (1.0 + 1.5 * c, _S3 * (r + 0.5 + 0.5 * (c & 1)))

    def geometry(self) -> dict:
        idx = self.index
        W = 1.5 * self.C + 0.5
        H = _S3 * self.R + (_S3 / 2 if self.C > 1 else 0.0)

        def clamp(x: float, y: float) -> list[float]:
            return [min(max(x, 0.0), W), min(max(y, 0.0), H)]

        polys, walls = [], []
        for cell in self.cells():
            cx, cy = self.position(cell)
            vs = [clamp(cx + math.cos(math.radians(60 * j)), cy - math.sin(math.radians(60 * j)))
                  for j in range(6)]
            polys.append(vs)
            a = idx[cell]
            for j, nb in enumerate(self._dirs[cell]):
                if nb is None:
                    walls.append({"a": a, "b": None, "pts": [vs[j], vs[(j + 1) % 6]]})
                elif a < idx[nb]:
                    walls.append({"a": a, "b": idx[nb], "pts": [vs[j], vs[(j + 1) % 6]]})
        return {"width": W, "height": H, "cells": polys, "walls": walls}

    # --- ROWS -----------------------------------------------------------
    def rows(self) -> Sequence[Sequence[Cell]]:
        return [[(r, c) for c in range(self.C)] for r in range(self.R)]

    def row_of(self, cell: Cell) -> int:
        return cell[0]

    def next_in_row(self, cell: Cell) -> Cell | None:
        r, c = cell
        return (r, c + 1) if c + 1 < self.C else None

    def prev_row_neighbors(self, cell: Cell) -> list[Cell]:
        return [n for n in self._nbrs[cell] if n[0] == cell[0] - 1]

    def next_row_neighbors(self, cell: Cell) -> list[Cell]:
        return [n for n in self._nbrs[cell] if n[0] == cell[0] + 1]

    # --- HEADINGS / METRIC ---------------------------------------------
    def heading(self, src: Cell, dst: Cell) -> float:
        p, q = self.position(src), self.position(dst)
        h = math.atan2(-(q[1] - p[1]), q[0] - p[0])
        return math.pi if h == -math.pi else h

    @staticmethod
    def _cube(cell: Cell) -> tuple[int, int, int]:
        r, c = cell
        z = r - (c - (c & 1)) // 2
        return c, -c - z, z

    def distance(self, a: Cell, b: Cell) -> float:
        (x1, y1, z1), (x2, y2, z2) = self._cube(a), self._cube(b)
        return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))
