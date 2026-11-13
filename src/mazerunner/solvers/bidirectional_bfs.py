"""Bidirectional BFS. Alternate whole-layer expansions from start and goal (smaller frontier first).

Reference: Pohl 1971. Optimal: the layer in which the frontiers meet is finished and the best
crossing edge is kept. Counters: nodes_expanded, frontier_max.
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
    "bidirectional-bfs", title="Bidirectional BFS", requires=(), phase=Phase.ROUND_HEX,
    tags=('optimal', 'omniscient'), implemented=True, reference="Pohl 1971",
)
class BidirectionalBFS(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        if start == goal:
            if tr.enabled:
                tr.emit("visit", start)
            return SolveResult(Outcome.SOLVED, [start], {"nodes_expanded": 1, "frontier_max": 1})
        # side 0 = forward from start, side 1 = backward from goal
        dist = ({start: 0}, {goal: 0})
        parent: tuple[dict[Cell, Cell | None], dict[Cell, Cell | None]] = (
            {start: None}, {goal: None})
        layer = ([start], [goal])
        expanded = 0
        fmax = 2
        if tr.enabled:
            tr.emit("frontier_add", start)
            tr.emit("frontier_add", goal)
        best: tuple[int, Cell, Cell] | None = None  # (length, cell on forward tree, cell on backward tree)
        while layer[0] and layer[1] and best is None:
            side = 0 if len(layer[0]) <= len(layer[1]) else 1
            own, other = dist[side], dist[1 - side]
            nxt: list[Cell] = []
            for c in layer[side]:
                expanded += 1
                if tr.enabled:
                    tr.emit("frontier_remove", c)
                    tr.emit("visit", c)
                for n in maze.passages(c):
                    if n in other:
                        total = own[c] + 1 + other[n]
                        if best is None or total < best[0]:
                            best = (total, c, n) if side == 0 else (total, n, c)
                    if n not in own:
                        own[n] = own[c] + 1
                        parent[side][n] = c
                        nxt.append(n)
                        if tr.enabled:
                            tr.emit("frontier_add", n)
            layer = (nxt, layer[1]) if side == 0 else (layer[0], nxt)
            fmax = max(fmax, len(layer[0]) + len(layer[1]))
        counters = {"nodes_expanded": expanded, "frontier_max": fmax}
        if best is None:
            return SolveResult(Outcome.FAILED, [], counters)
        _, f_cell, b_cell = best
        path = build_path(parent[0], f_cell)
        path.extend(reversed(build_path(parent[1], b_cell)))
        return SolveResult(Outcome.SOLVED, path, counters)
