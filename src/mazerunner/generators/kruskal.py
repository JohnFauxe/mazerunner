"""Randomized Kruskal's. Shuffled edges + union-find.

Reference: Kruskal 1956. Notes: docs/algorithms/generation.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "kruskal", title="Randomized Kruskal's", requires=(), phase=Phase.ROUND_HEX,
    tags=(), reference="Kruskal 1956",
)
class Kruskal(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("kruskal: phase ROUND_HEX")
