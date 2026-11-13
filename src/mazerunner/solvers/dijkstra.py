"""Dijkstra. Uses maze.cost() (unit cost unless weights are set). Lazy-deletion heap.

Reference: Dijkstra 1959. Counters: nodes_expanded, frontier_max.
"""
from __future__ import annotations

import heapq
import random
from itertools import count

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.topology import Cell
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult
from mazerunner.solvers.bfs import build_path


@solvers.register(
    "dijkstra", title="Dijkstra", requires=(), phase=Phase.MVP,
    tags=('optimal', 'weighted', 'omniscient'), implemented=True, reference="Dijkstra 1959",
)
class Dijkstra(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        dist: dict[Cell, float] = {start: 0.0}
        parent: dict[Cell, Cell | None] = {start: None}
        done: set[Cell] = set()
        tie = count()
        heap = [(0.0, next(tie), start)]
        expanded = fmax = 0
        if tr.enabled:
            tr.emit("frontier_add", start)
        while heap:
            fmax = max(fmax, len(heap))
            d, _, c = heapq.heappop(heap)
            if c in done:
                continue
            done.add(c)
            expanded += 1
            if tr.enabled:
                tr.emit("frontier_remove", c)
                tr.emit("visit", c)
            if c == goal:
                return SolveResult(Outcome.SOLVED, build_path(parent, goal),
                                   {"nodes_expanded": expanded, "frontier_max": fmax})
            for n in maze.passages(c):
                nd = d + maze.cost(c, n)
                if n not in done and nd < dist.get(n, float("inf")):
                    dist[n] = nd
                    parent[n] = c
                    heapq.heappush(heap, (nd, next(tie), n))
                    if tr.enabled:
                        tr.emit("frontier_add", n)
        return SolveResult(Outcome.FAILED, [], {"nodes_expanded": expanded, "frontier_max": fmax})
