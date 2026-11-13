"""Binary Tree: for every cell, carve north or east (random), if they exist.

Reference: Buck, MfP ch.2. Notes: docs/algorithms/generation.md
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait
from mazerunner.generators.base import Generator


@generators.register(
    "binary-tree", title="Binary Tree", requires=(Trait.ORTHOGONAL,), phase=Phase.MVP,
    implemented=True, tags=('stateless',), reference="Buck, MfP ch.2",
)
class BinaryTree(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        tr = self.tracer
        for cell in topo.cell_list:
            if tr.enabled:
                tr.emit("current", cell)
            options = [n for d in ("N", "E") if (n := topo.axis_neighbor(cell, d)) is not None]
            if options:
                maze.link(cell, options[rng.randrange(len(options))])
