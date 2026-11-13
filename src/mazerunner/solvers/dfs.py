"""Depth-first search. Iterative with visited set.

Reference: —. Notes: docs/algorithms/solving.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "dfs", title="Depth-first search", requires=(), phase=Phase.MVP,
    tags=('omniscient',), reference="—",
)
class DFS(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("dfs: phase MVP")
