"""A*. Heuristic = topology.distance(); param heuristic_scale for weighted A*.

Reference: Hart, Nilsson, Raphael 1968. Notes: docs/algorithms/solving.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "astar", title="A*", requires=(Trait.METRIC,), phase=Phase.MVP,
    tags=('optimal', 'omniscient'), reference="Hart, Nilsson, Raphael 1968",
)
class AStar(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("astar: phase MVP")
