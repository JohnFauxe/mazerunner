"""Wall follower (left/right hand). param hand='left'|'right'. Pick next exit in cyclic order relative to arrival edge.

Reference: Pullen, Think Labyrinth. Notes: docs/algorithms/solving.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "wall-follower", title="Wall follower (left/right hand)", requires=(Trait.PLANAR,), phase=Phase.MVP,
    tags=('agent',), reference="Pullen, Think Labyrinth",
)
class WallFollower(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        raise NotImplementedError("wall-follower: phase MVP")
