"""Bidirectional BFS. Alternate frontiers from start and goal.

Reference: Pohl 1971. Notes: docs/algorithms/solving.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import OmniscientSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "bidirectional-bfs", title="Bidirectional BFS", requires=(), phase=Phase.ROUND_HEX,
    tags=('optimal', 'omniscient'), reference="Pohl 1971",
)
class BidirectionalBFS(OmniscientSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        raise NotImplementedError("bidirectional-bfs: phase ROUND_HEX")
