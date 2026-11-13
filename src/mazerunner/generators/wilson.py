"""Wilson's (loop-erased random walk). Loop-erased random walks from unvisited cells until they hit the tree.

Reference: Wilson, STOC 1996. Notes: docs/algorithms/generation.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "wilson", title="Wilson's (loop-erased random walk)", requires=(), phase=Phase.MVP,
    tags=('uniform',), reference="Wilson, STOC 1996",
)
class Wilson(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("wilson: phase MVP")
