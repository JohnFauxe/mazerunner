"""Jump Point Search. Mostly benefits open/braided grids.

Reference: Harabor & Grastien 2011. Notes: docs/algorithms/solving.md
Status: placeholder (phase PLACEHOLDER).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "jps", title="Jump Point Search", requires=(Trait.UNIFORM_GRID,), phase=Phase.PLACEHOLDER,
    tags=('optimal', 'omniscient'), reference="Harabor & Grastien 2011",
)
class JumpPointSearch(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("jps: phase PLACEHOLDER")
