"""Binary Tree. Each cell links north or east at random.

Reference: Buck, MfP ch.2. Notes: docs/algorithms/generation.md
Status: placeholder (phase MVP).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "binary-tree", title="Binary Tree", requires=(Trait.ORTHOGONAL,), phase=Phase.MVP,
    tags=('stateless',), reference="Buck, MfP ch.2",
)
class BinaryTree(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("binary-tree: phase MVP")
