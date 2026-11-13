"""Eller's. Row-at-a-time set merging with mandatory downward passages.

Reference: Eller 1982; Pullen, Think Labyrinth. Notes: docs/algorithms/generation.md
Status: placeholder (phase ANALYSIS).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "eller", title="Eller's", requires=(Trait.ROWS,), phase=Phase.ANALYSIS,
    tags=('streaming',), reference="Eller 1982; Pullen, Think Labyrinth",
)
class Eller(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("eller: phase ANALYSIS")
