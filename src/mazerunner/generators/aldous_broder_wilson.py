"""Aldous–Broder → Wilson hybrid: Aldous–Broder (fast early, slow to find the last cells)
until a fraction `switch` (default 1/3) of cells is visited, then Wilson's (slow early,
fast late). Both are uniform, so the hybrid is uniform. Reference: Buck, MfP ch.4 notes.
"""
import math
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.aldous_broder import aldous_broder_walk
from mazerunner.generators.base import Generator
from mazerunner.generators.wilson import wilson_complete


@generators.register(
    "ab-wilson-hybrid", title="Aldous–Broder → Wilson hybrid", requires=(), phase=Phase.PLACEHOLDER,
    implemented=True, tags=('uniform',), reference="Buck, MfP ch.4 notes",
)
class AldousBroderWilson(Generator):

    def __init__(self, switch: float = 1 / 3, **params) -> None:
        super().__init__(switch=switch, **params)
        self.switch = switch

    def carve(self, maze: Maze, rng: random.Random) -> None:
        cells = maze.topology.cell_list
        n = len(cells)
        if not n:
            return
        start = cells[rng.randrange(n)]
        visited = {start}
        target = min(n, max(1, math.ceil(self.switch * n)))
        aldous_broder_walk(self, maze, rng, start, visited, target)
        if len(visited) < n:
            if self.tracer.enabled:
                self.tracer.emit("phase", label="wilson")
            wilson_complete(self, maze, rng, visited)
