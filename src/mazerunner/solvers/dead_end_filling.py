"""Dead-end filling. Repeatedly fill degree-1 cells (except endpoints); remainder is the solution on perfect mazes.

Reference: Pullen, Think Labyrinth. Notes: docs/algorithms/solving.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "dead-end-filling", title="Dead-end filling", requires=(), phase=Phase.ROUND_HEX,
    tags=('omniscient',), reference="Pullen, Think Labyrinth",
)
class DeadEndFilling(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("dead-end-filling: phase ROUND_HEX")
