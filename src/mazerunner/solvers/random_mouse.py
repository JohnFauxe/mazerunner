"""Random mouse. Random exit, avoid immediate reversal unless dead end.

Reference: Pullen, Think Labyrinth. Notes: docs/algorithms/solving.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "random-mouse", title="Random mouse", requires=(), phase=Phase.MVP,
    tags=('agent',), reference="Pullen, Think Labyrinth",
)
class RandomMouse(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        raise NotImplementedError("random-mouse: phase MVP")
