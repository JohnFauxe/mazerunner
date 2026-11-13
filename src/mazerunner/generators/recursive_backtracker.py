"""Recursive Backtracker (randomized DFS). Random walk to unvisited neighbors with an explicit stack; backtrack when stuck.

Reference: Buck, Mazes for Programmers ch.5. Notes: docs/algorithms/generation.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "recursive-backtracker", title="Recursive Backtracker (randomized DFS)", requires=(), phase=Phase.MVP,
    tags=(), reference="Buck, Mazes for Programmers ch.5",
)
class RecursiveBacktracker(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("recursive-backtracker: phase MVP")
