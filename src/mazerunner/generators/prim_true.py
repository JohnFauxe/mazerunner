"""Prim's (true, random weights). Random cell weights then Prim's MST with a priority queue.

Reference: Prim 1957; Buck, MfP ch.11. Notes: docs/algorithms/generation.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "prim-true", title="Prim's (true, random weights)", requires=(), phase=Phase.ROUND_HEX,
    tags=(), reference="Prim 1957; Buck, MfP ch.11",
)
class PrimTrue(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("prim-true: phase ROUND_HEX")
