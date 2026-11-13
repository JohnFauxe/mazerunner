"""A*. Heuristic = topology.distance(); param heuristic_scale (default 1.0, >1 = weighted A*).

Reference: Hart, Nilsson, Raphael 1968. Counters: nodes_expanded, frontier_max, reopened.
With scale 1 and an admissible heuristic the path is optimal; scale > 1 trades optimality
for fewer expansions. Closed nodes are re-opened if a cheaper route is found.
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
    "astar", title="A*", requires=(Trait.METRIC,), phase=Phase.MVP,
    tags=('optimal', 'omniscient'), implemented=True, reference="Hart, Nilsson, Raphael 1968",
)
class AStar(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        topo = maze.topology
        w = float(self.params.get("heuristic_scale", 1.0))
        h = (lambda c: w * topo.distance(c, goal)) if topo.has(Trait.METRIC) else (lambda c: 0.0)
        g: dict[Cell, float] = {start: 0.0}
        parent: dict[Cell, Cell | None] = {start: None}
        closed: set[Cell] = set()
        tie = count()
        heap = [(h(start), next(tie), 0.0, start)]
        expanded = fmax = reopened = 0
        if tr.enabled:
            tr.emit("frontier_add", start)
        while heap:
            fmax = max(fmax, len(heap))
            _, _, gc, c = heapq.heappop(heap)
            if gc > g[c]:
                continue  # stale entry
            if c in closed:
                continue
            closed.add(c)
            expanded += 1
            if tr.enabled:
                tr.emit("frontier_remove", c)
                tr.emit("visit", c)
            if c == goal:
                return SolveResult(Outcome.SOLVED, build_path(parent, goal),
                                   {"nodes_expanded": expanded, "frontier_max": fmax,
                                    "reopened": reopened})
            for n in maze.passages(c):
                ng = gc + maze.cost(c, n)
                if ng < g.get(n, float("inf")):
                    if n in closed:
                        closed.discard(n)
                        reopened += 1
                    g[n] = ng
                    parent[n] = c
                    heapq.heappush(heap, (ng + h(n), next(tie), ng, n))
                    if tr.enabled:
                        tr.emit("frontier_add", n)
        return SolveResult(Outcome.FAILED, [], {"nodes_expanded": expanded, "frontier_max": fmax,
                                                "reopened": reopened})
