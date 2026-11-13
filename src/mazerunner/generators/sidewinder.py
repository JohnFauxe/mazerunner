"""Sidewinder. Row-wise runs; close each run by linking one member to the previous row.

Reference: Buck, MfP ch.2. Notes: docs/algorithms/generation.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "sidewinder", title="Sidewinder", requires=(Trait.ROWS,), phase=Phase.MVP,
    tags=(), reference="Buck, MfP ch.2",
)
class Sidewinder(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("sidewinder: phase MVP")
