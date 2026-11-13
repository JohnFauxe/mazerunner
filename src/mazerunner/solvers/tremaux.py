"""Trémaux's algorithm. Chalk marks via probe.mark()/marks().

Reference: Lucas 1882. Notes: docs/algorithms/solving.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "tremaux", title="Trémaux's algorithm", requires=(), phase=Phase.ROUND_HEX,
    tags=('complete', 'agent'), reference="Lucas 1882",
)
class Tremaux(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        raise NotImplementedError("tremaux: phase ROUND_HEX")
