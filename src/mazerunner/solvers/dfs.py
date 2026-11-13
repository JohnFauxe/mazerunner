"""Depth-first search. Iterative with visited set. Counters: nodes_expanded, frontier_max.

Notes: docs/algorithms/solving.md
"""
from __future__ import annotations

import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.topology import Cell
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult
from mazerunner.solvers.bfs import build_path


@solvers.register(
    "dfs", title="Depth-first search", requires=(), phase=Phase.MVP,
    tags=('omniscient',), implemented=True, reference="—",
)
class DFS(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        parent: dict[Cell, Cell | None] = {start: None}
        stack = [start]
        expanded = fmax = 0
        if tr.enabled:
            tr.emit("frontier_add", start)
        while stack:
            fmax = max(fmax, len(stack))
            c = stack.pop()
            expanded += 1
            if tr.enabled:
                tr.emit("frontier_remove", c)
                tr.emit("visit", c)
            if c == goal:
                return SolveResult(Outcome.SOLVED, build_path(parent, goal),
                                   {"nodes_expanded": expanded, "frontier_max": fmax})
            # reversed so the first passage in topology order is explored first
            for n in reversed(maze.passages(c)):
                if n not in parent:
                    parent[n] = c
                    stack.append(n)
                    if tr.enabled:
                        tr.emit("frontier_add", n)
        return SolveResult(Outcome.FAILED, [], {"nodes_expanded": expanded, "frontier_max": fmax})
