"""Greedy best-first. Priority = h only (topology.distance to the goal). Not optimal.

Counters: nodes_expanded, frontier_max.
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
from mazerunner.solvers.bfs import build_path


@solvers.register(
    "greedy", title="Greedy best-first", requires=(Trait.METRIC,), phase=Phase.ROUND_HEX,
    tags=('omniscient',), implemented=True, reference="—",
)
class Greedy(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        topo = maze.topology
        h = (lambda c: topo.distance(c, goal)) if topo.has(Trait.METRIC) else (lambda c: 0.0)
        parent: dict[Cell, Cell | None] = {start: None}
        done: set[Cell] = set()
        tie = count()
        heap = [(h(start), next(tie), start)]
        expanded = fmax = 0
        if tr.enabled:
            tr.emit("frontier_add", start)
        while heap:
            fmax = max(fmax, len(heap))
            _, _, c = heapq.heappop(heap)
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
                if n not in parent:
                    parent[n] = c
                    heapq.heappush(heap, (h(n), next(tie), n))
                    if tr.enabled:
                        tr.emit("frontier_add", n)
        return SolveResult(Outcome.FAILED, [], {"nodes_expanded": expanded, "frontier_max": fmax})
