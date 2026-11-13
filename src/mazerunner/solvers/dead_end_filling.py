"""Dead-end filling. Repeatedly fill degree-1 cells (except endpoints); remainder is the solution
on perfect mazes. On braided mazes loops survive the filling, so the route is then extracted
with a BFS over the unfilled cells (which yields a valid, shortest-among-remaining path).

Reference: Pullen, Think Labyrinth. Counters: nodes_expanded (extraction), cells_filled.
Emits "fill" per filled cell.
"""
from __future__ import annotations

import random
from collections import deque

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.topology import Cell
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult
from mazerunner.solvers.bfs import build_path


@solvers.register(
    "dead-end-filling", title="Dead-end filling", requires=(), phase=Phase.ROUND_HEX,
    tags=('omniscient',), implemented=True, reference="Pullen, Think Labyrinth",
)
class DeadEndFilling(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        keep = {start, goal}
        deg = {c: len(maze.passages(c)) for c in maze.topology.cells()}
        filled: set[Cell] = set()
        queue = deque(c for c, d in deg.items() if d == 1 and c not in keep)
        while queue:
            c = queue.popleft()
            filled.add(c)
            if tr.enabled:
                tr.emit("fill", c)
            for n in maze.passages(c):
                if n not in filled:
                    deg[n] -= 1
                    if deg[n] == 1 and n not in keep:
                        queue.append(n)
        # extract the route from what is left
        parent: dict[Cell, Cell | None] = {start: None}
        q = deque([start])
        expanded = 0
        while q:
            c = q.popleft()
            expanded += 1
            if tr.enabled:
                tr.emit("visit", c)
            if c == goal:
                return SolveResult(Outcome.SOLVED, build_path(parent, goal),
                                   {"nodes_expanded": expanded, "cells_filled": len(filled)})
            for n in maze.passages(c):
                if n not in filled and n not in parent:
                    parent[n] = c
                    q.append(n)
        return SolveResult(Outcome.FAILED, [], {"nodes_expanded": expanded,
                                                "cells_filled": len(filled)})
