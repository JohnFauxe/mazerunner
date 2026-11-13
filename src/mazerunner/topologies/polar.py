"""Polar (round / theta) topology. Cell = (ring, index).

Notes: docs/algorithms/topologies.md. Constructor args: (rings,)

Construction (Buck, *Mazes for Programmers* ch.7): ring 0 is one centre cell; ring r>0
starts from the previous ring's cell count and multiplies it by
``round((2*pi*r / prev_count) / 1)`` (ring height 1) so cells stay roughly square.

Conventions
-----------
* Ring r occupies radii [r, r+1] (ring 0 is a disc of radius 1); the centre is at (R, R), R = rings.
* Cell index i of a ring with n cells covers maths angle ``theta0 + 2*pi*i/n .. +2*pi/n`` where
  theta0 is shared by all rings (so children nest in their parent sector) and chosen so that
  outer-ring cell 0 is *centred* on angle pi (west). Indices therefore increase counter-clockwise
  on screen, and ``next_in_row`` is index + 1 (CCW), None on the last index (no wrap).
* distance = |ring_a - ring_b|: every edge changes the ring by at most 1, so this is a lower bound
  on the number of steps in any maze (admissible).
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence

from mazerunner.core.registry import Phase, topologies
from mazerunner.core.topology import Cell, Topology
from mazerunner.core.traits import Trait

_TAU = 2 * math.pi
_ARC_STEP = math.radians(10)


@topologies.register("polar", title="Polar (round / theta)", requires=(), phase=Phase.ROUND_HEX,
                     implemented=True)
class PolarGrid(Topology):
    name = "polar"
    traits = frozenset({Trait.ROWS, Trait.PLANAR, Trait.HEADINGS, Trait.METRIC})

    def __init__(self, rings: int) -> None:
        if rings < 1:
            raise ValueError("polar grid needs at least 1 ring")
        self.rings = rings
        self.args = (rings,)
        counts = [1]
        ratios = [1]
        for r in range(1, rings):
            ratio = max(1, round(_TAU * r / counts[-1]))
            ratios.append(ratio)
            counts.append(counts[-1] * ratio)
        self._counts, self._ratios = counts, ratios
        self._theta0 = math.pi - math.pi / counts[-1]
        self._nbrs: dict[Cell, tuple[Cell, ...]] = {}
        self._prev: dict[Cell, list[Cell]] = {}
        self._next: dict[Cell, list[Cell]] = {}
        for r in range(rings):
            n = counts[r]
            for i in range(n):
                prev = [] if r == 0 else [(r - 1, i // ratios[r])]
                nxt = [] if r == rings - 1 else [
                    (r + 1, i * ratios[r + 1] + k) for k in range(ratios[r + 1])]
                side = []
                if n > 1:
                    side.append((r, (i + 1) % n))
                    if n > 2:
                        side.append((r, (i - 1) % n))
                self._prev[(r, i)], self._next[(r, i)] = prev, nxt
                allns = prev + nxt + side
                p = self.position((r, i))
                allns.sort(key=lambda q: self._angle(p, self.position(q)))
                self._nbrs[(r, i)] = tuple(allns)

    @staticmethod
    def _angle(p: tuple[float, float], q: tuple[float, float]) -> float:
        """Maths-convention angle (screen y flipped) of p->q in [0, 2*pi)."""
        return math.atan2(-(q[1] - p[1]), q[0] - p[0]) % _TAU

    # --- core -----------------------------------------------------------
    def cells(self) -> Iterator[Cell]:
        for r, n in enumerate(self._counts):
            for i in range(n):
                yield (r, i)

    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        return self._nbrs[cell]

    def __len__(self) -> int:
        return sum(self._counts)

    def boundary(self) -> list[Cell]:
        r = self.rings - 1
        return [(r, i) for i in range(self._counts[r])]  # cell 0 centred on angle pi, CCW

    def _span(self, cell: Cell) -> tuple[float, float]:
        r, i = cell
        w = _TAU / self._counts[r]
        return self._theta0 + i * w, self._theta0 + (i + 1) * w

    def _pt(self, rad: float, t: float) -> list[float]:
        R = self.rings
        x = min(max(R + rad * math.cos(t), 0.0), 2.0 * R)
        y = min(max(R - rad * math.sin(t), 0.0), 2.0 * R)
        return [x, y]

    def _arc(self, rad: float, t0: float, t1: float) -> list[list[float]]:
        k = max(1, math.ceil(abs(t1 - t0) / _ARC_STEP - 1e-9))
        return [self._pt(rad, t0 + (t1 - t0) * j / k) for j in range(k + 1)]

    def position(self, cell: Cell) -> tuple[float, float]:
        r, i = cell
        if r == 0:
            return (float(self.rings), float(self.rings))
        t0, t1 = self._span(cell)
        x, y = self._pt(r + 0.5, (t0 + t1) / 2)
        return (x, y)

    def geometry(self) -> dict:
        idx = self.index
        polys: list[list[list[float]]] = []
        walls: list[dict] = []
        last = self.rings - 1
        for cell in self.cells():
            r, i = cell
            a = idx[cell]
            n = self._counts[r]
            if r == 0:
                polys.append(self._arc(1.0, 0.0, _TAU)[:-1])
                if last == 0:
                    walls.append({"a": a, "b": None, "pts": self._arc(1.0, 0.0, _TAU)})
                continue
            t0, t1 = self._span(cell)
            polys.append(self._arc(r + 1, t0, t1) + self._arc(r, t1, t0))
            walls.append({"a": a, "b": idx[self._prev[cell][0]], "pts": self._arc(r, t0, t1)})
            if n > 2 or (n == 2 and i == 0):
                walls.append({"a": a, "b": idx[(r, (i + 1) % n)],
                              "pts": [self._pt(r, t1), self._pt(r + 1, t1)]})
            if r == last:
                walls.append({"a": a, "b": None, "pts": self._arc(r + 1, t0, t1)})
        s = 2.0 * self.rings
        return {"width": s, "height": s, "cells": polys, "walls": walls}

    # --- ROWS -----------------------------------------------------------
    def rows(self) -> Sequence[Sequence[Cell]]:
        return [[(r, i) for i in range(n)] for r, n in enumerate(self._counts)]

    def row_of(self, cell: Cell) -> int:
        return cell[0]

    def next_in_row(self, cell: Cell) -> Cell | None:
        r, i = cell
        return (r, i + 1) if i + 1 < self._counts[r] else None

    def prev_row_neighbors(self, cell: Cell) -> list[Cell]:
        return list(self._prev[cell])

    def next_row_neighbors(self, cell: Cell) -> list[Cell]:
        return list(self._next[cell])

    # --- HEADINGS / METRIC ---------------------------------------------
    def heading(self, src: Cell, dst: Cell) -> float:
        p, q = self.position(src), self.position(dst)
        h = math.atan2(-(q[1] - p[1]), q[0] - p[0])
        return math.pi if h == -math.pi else h

    def distance(self, a: Cell, b: Cell) -> float:
        return abs(a[0] - b[0])
