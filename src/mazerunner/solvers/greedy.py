"""Greedy best-first. Priority = h only.

Reference: —. Notes: docs/algorithms/solving.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "greedy", title="Greedy best-first", requires=(Trait.METRIC,), phase=Phase.ROUND_HEX,
    tags=('omniscient',), reference="—",
)
class GreedyBestFirst(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("greedy: phase ROUND_HEX")
