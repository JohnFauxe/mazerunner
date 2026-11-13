"""Chain algorithm. Follow straight line to goal, wall-following around obstacles.

Reference: Pullen, Think Labyrinth. Notes: docs/algorithms/solving.md
Status: placeholder (phase PLACEHOLDER).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "chain", title="Chain algorithm", requires=(Trait.METRIC,), phase=Phase.PLACEHOLDER,
    tags=('agent',), reference="Pullen, Think Labyrinth",
)
class Chain(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        raise NotImplementedError("chain: phase PLACEHOLDER")
