"""Recursive Division. Start open; recursively bisect with walls containing one gap. Overrides generate().

Reference: Buck, MfP ch.12. Notes: docs/algorithms/generation.md
Status: placeholder (phase ANALYSIS).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "recursive-division", title="Recursive Division", requires=(Trait.RECTANGULAR,), phase=Phase.ANALYSIS,
    tags=('wall-adding',), reference="Buck, MfP ch.12",
)
class RecursiveDivision(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("recursive-division: phase ANALYSIS")
