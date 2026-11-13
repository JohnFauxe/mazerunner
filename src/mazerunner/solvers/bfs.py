"""Breadth-first search (Lee). Counters: nodes_expanded, frontier_max.

Reference: Lee 1961. Notes: docs/algorithms/solving.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "bfs", title="Breadth-first search (Lee)", requires=(), phase=Phase.MVP,
    tags=('optimal', 'omniscient'), reference="Lee 1961",
)
class BFS(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("bfs: phase MVP")
