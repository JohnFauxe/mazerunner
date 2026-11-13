"""IDA*. Iterative deepening on f = g + h.

Reference: Korf 1985. Notes: docs/algorithms/solving.md
Status: placeholder (phase ANALYSIS).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "idastar", title="IDA*", requires=(Trait.METRIC,), phase=Phase.ANALYSIS,
    tags=('optimal', 'omniscient'), reference="Korf 1985",
)
class IDAStar(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("idastar: phase ANALYSIS")
