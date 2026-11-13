"""Aldous–Broder: unbiased random walk; carve whenever the walk enters a new cell.

Uniform over spanning trees. Reference: Aldous 1990; Broder 1989.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


def aldous_broder_walk(gen: Generator, maze: Maze, rng: random.Random, cur, visited: set,
                       target: int) -> tuple:
    """Continue an Aldous–Broder walk from `cur` until `len(visited) >= target`.
    Returns the current cell."""
    topo = maze.topology
    tr = gen.tracer
    steps = 0
    while len(visited) < target:
        nbrs = topo.neighbors(cur)
        nxt = nbrs[rng.randrange(len(nbrs))]
        steps += 1
        if tr.enabled:
            tr.emit("walk", cur, nxt)
        if nxt not in visited:
            maze.link(cur, nxt)
            visited.add(nxt)
        cur = nxt
    gen.bump("walk_steps", steps)
    return cur


@generators.register(
    "aldous-broder", title="Aldous–Broder", requires=(), phase=Phase.MVP,
    implemented=True, tags=('uniform',), reference="Aldous 1990; Broder 1989",
)
class AldousBroder(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        cells = maze.topology.cell_list
        if not cells:
            return
        start = cells[rng.randrange(len(cells))]
        aldous_broder_walk(self, maze, rng, start, {start}, len(cells))
