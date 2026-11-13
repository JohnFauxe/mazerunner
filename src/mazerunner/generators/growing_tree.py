"""Growing Tree. Cell list with pluggable pick strategy (params: strategy='newest'|'random'|'oldest'|'mix', mix=0.5).

Reference: Buck blog 2011; MfP ch.11. Notes: docs/algorithms/generation.md
Status: placeholder (phase ROUND_HEX).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "growing-tree", title="Growing Tree", requires=(), phase=Phase.ROUND_HEX,
    tags=('tunable',), reference="Buck blog 2011; MfP ch.11",
)
class GrowingTree(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("growing-tree: phase ROUND_HEX")
