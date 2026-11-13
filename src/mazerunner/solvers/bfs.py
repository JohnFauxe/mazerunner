"""Breadth-first search (Lee). Counters: nodes_expanded, frontier_max.

Reference: Lee 1961. Notes: docs/algorithms/solving.md
"""
from __future__ import annotations

import random
from collections import deque

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.topology import Cell
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult


def build_path(parent: dict, end: Cell) -> list[Cell]:
    """Walk a parent map (root maps to None) back from `end`; returns root..end."""
    path = [end]
    while (p := parent[path[-1]]) is not None:
        path.append(p)
    path.reverse()
    return path


@solvers.register(
    "bfs", title="Breadth-first search (Lee)", requires=(), phase=Phase.MVP,
    tags=('optimal', 'omniscient'), implemented=True, reference="Lee 1961",
)
class BFS(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        parent: dict[Cell, Cell | None] = {start: None}
        q = deque([start])
        expanded = fmax = 0
        if tr.enabled:
            tr.emit("frontier_add", start)
        while q:
            fmax = max(fmax, len(q))
            c = q.popleft()
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
                    q.append(n)
                    if tr.enabled:
                        tr.emit("frontier_add", n)
        return SolveResult(Outcome.FAILED, [], {"nodes_expanded": expanded, "frontier_max": fmax})
