"""Hunt-and-Kill. Random walk; when stuck, scan for an unvisited cell adjacent to the maze.

Reference: Buck, MfP ch.5. Notes: docs/algorithms/generation.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "hunt-and-kill", title="Hunt-and-Kill", requires=(), phase=Phase.ROUND_HEX,
    tags=(), reference="Buck, MfP ch.5",
)
class HuntAndKill(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("hunt-and-kill: phase ROUND_HEX")
