"""Pledge algorithm. Preferred heading + wall following with turn-sum counter.

Reference: Abelson & diSessa 1980. Notes: docs/algorithms/solving.md
Status: placeholder (phase ANALYSIS).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "pledge", title="Pledge algorithm", requires=(Trait.PLANAR, Trait.HEADINGS), phase=Phase.ANALYSIS,
    tags=('escape', 'agent'), reference="Abelson & diSessa 1980",
)
class Pledge(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        raise NotImplementedError("pledge: phase ANALYSIS")
