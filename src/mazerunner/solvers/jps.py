"""Jump Point Search (Harabor & Grastien 2011) on 4-connected uniform grids with edge walls.

Passage between adjacent cells is maze.linked(a, b). In a maze every open side branch is a
"forced neighbour", so a jump scans straight along a corridor until it reaches the goal, a cell
with a perpendicular opening (a jump point) or a dead end (no jump point). A* with the
Manhattan heuristic then runs over jump points only; corridors are expanded back into cells
when the path is rebuilt. Optimal (matches BFS length). Counters: nodes_expanded (jump points
expanded), frontier_max, jumps, cells_scanned.
"""
from __future__ import annotations

import heapq
import random
from itertools import count

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.topology import Cell
from mazerunner.core.traits import Trait
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult

_OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}
_PERP = {"N": ("E", "W"), "S": ("E", "W"), "E": ("N", "S"), "W": ("N", "S")}


@solvers.register(
    "jps", title="Jump Point Search", requires=(Trait.UNIFORM_GRID,), phase=Phase.PLACEHOLDER,
    tags=('optimal', 'omniscient'), implemented=True, reference="Harabor & Grastien 2011",
)
class JPS(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        topo = maze.topology
        start, goal = maze.start, maze.goal
        stats = {"jumps": 0, "cells_scanned": 0}

        def step(c: Cell, d: str) -> Cell | None:
            n = topo.axis_neighbor(c, d)
            return n if n is not None and maze.linked(c, n) else None

        def jump(c: Cell, d: str) -> tuple[Cell, int] | None:
            stats["jumps"] += 1
            steps = 0
            while True:
                n = step(c, d)
                if n is None:
                    return None
                c = n
                steps += 1
                stats["cells_scanned"] += 1
                if c == goal or any(step(c, p) is not None for p in _PERP[d]):
                    return c, steps

        g: dict[Cell, float] = {start: 0.0}
        parent: dict[Cell, tuple[Cell, str] | None] = {start: None}
        arrived: dict[Cell, str | None] = {start: None}
        closed: set[Cell] = set()
        tie = count()
        heap = [(topo.distance(start, goal), next(tie), 0.0, start)]
        expanded = fmax = 0
        if tr.enabled:
            tr.emit("frontier_add", start)
        found = False
        while heap:
            fmax = max(fmax, len(heap))
            _, _, gc, c = heapq.heappop(heap)
            if c in closed or gc > g[c]:
                continue
            closed.add(c)
            expanded += 1
            if tr.enabled:
                tr.emit("frontier_remove", c)
                tr.emit("visit", c)
            if c == goal:
                found = True
                break
            back = _OPP[arrived[c]] if arrived[c] else None
            for d in ("N", "E", "S", "W"):
                if d == back:
                    continue
                jp = jump(c, d)
                if jp is None:
                    continue
                n, steps = jp
                ng = gc + steps
                if n not in closed and ng < g.get(n, float("inf")):
                    g[n] = ng
                    parent[n] = (c, d)
                    arrived[n] = d
                    heapq.heappush(heap, (ng + topo.distance(n, goal), next(tie), ng, n))
                    if tr.enabled:
                        tr.emit("frontier_add", n)
        counters = {"nodes_expanded": expanded, "frontier_max": fmax, **stats}
        if not found:
            return SolveResult(Outcome.FAILED, [], counters)
        # rebuild: expand each jump segment back into individual cells
        segs: list[tuple[Cell, Cell, str]] = []
        c = goal
        while (p := parent[c]) is not None:
            segs.append((p[0], c, p[1]))
            c = p[0]
        path: list[Cell] = [start]
        for a, b, d in reversed(segs):
            cur = a
            while cur != b:
                cur = topo.axis_neighbor(cur, d)
                path.append(cur)
        return SolveResult(Outcome.SOLVED, path, counters)
