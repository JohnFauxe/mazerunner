"""Aldous–Broder. Random walk; carve on first entry to each cell. Counter: walk_steps.

Reference: Aldous 1990; Broder 1989. Notes: docs/algorithms/generation.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "aldous-broder", title="Aldous–Broder", requires=(), phase=Phase.MVP,
    tags=('uniform',), reference="Aldous 1990; Broder 1989",
)
class AldousBroder(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("aldous-broder: phase MVP")
