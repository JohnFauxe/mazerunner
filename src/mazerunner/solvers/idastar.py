"""IDA*. Iterative deepening on f = g + h with an explicit stack (no recursion).

Reference: Korf 1985. Only the current path is stored (cycle check against it), so on heavily
braided mazes it can re-expand a lot; params: max_nodes (default 5_000_000, then TIMEOUT).
The bound never needs to exceed the number of cells, which caps the iteration count.
Counters: nodes_expanded, frontier_max (= deepest stack), iterations. Emits "phase" per bound.
"""
from __future__ import annotations

import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.topology import Cell
from mazerunner.core.traits import Trait
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult


@solvers.register(
    "idastar", title="IDA*", requires=(Trait.METRIC,), phase=Phase.ANALYSIS,
    tags=('optimal', 'omniscient'), implemented=True, reference="Korf 1985",
)
class IDAStar(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        tr = self.tracer
        start, goal = maze.start, maze.goal
        topo = maze.topology
        h = (lambda c: topo.distance(c, goal)) if topo.has(Trait.METRIC) else (lambda c: 0.0)
        max_nodes = int(self.params.get("max_nodes", 5_000_000))
        inf = float("inf")
        bound = h(start)
        expanded = fmax = iterations = 0
        limit = len(topo) + h(start) + 1  # an optimal path has f <= n - 1
        while bound <= limit:
            iterations += 1
            if tr.enabled:
                tr.emit("phase", label=f"bound {bound:g}")
            path: list[Cell] = [start]
            gs = [0.0]
            iters = [iter(maze.passages(start))]
            on_path = {start}
            nxt_bound = inf
            expanded += 1
            if tr.enabled:
                tr.emit("visit", start)
            if start == goal:
                return SolveResult(Outcome.SOLVED, path, {
                    "nodes_expanded": expanded, "frontier_max": 1, "iterations": iterations})
            while iters:
                c = path[-1]
                for n in iters[-1]:
                    if n in on_path:
                        continue
                    ng = gs[-1] + maze.cost(c, n)
                    f = ng + h(n)
                    if f > bound:
                        nxt_bound = min(nxt_bound, f)
                        continue
                    expanded += 1
                    if tr.enabled:
                        tr.emit("visit", n)
                    if n == goal:
                        path.append(n)
                        return SolveResult(Outcome.SOLVED, path, {
                            "nodes_expanded": expanded, "frontier_max": max(fmax, len(path)),
                            "iterations": iterations})
                    if expanded >= max_nodes:
                        return SolveResult(Outcome.TIMEOUT, [], {
                            "nodes_expanded": expanded, "frontier_max": fmax,
                            "iterations": iterations})
                    path.append(n)
                    gs.append(ng)
                    on_path.add(n)
                    iters.append(iter(maze.passages(n)))
                    fmax = max(fmax, len(path))
                    break
                else:  # iterator exhausted: backtrack
                    iters.pop()
                    on_path.discard(path.pop())
                    gs.pop()
            if nxt_bound == inf:
                break
            bound = nxt_bound
        return SolveResult(Outcome.FAILED, [], {"nodes_expanded": expanded, "frontier_max": fmax,
                                                "iterations": iterations})
