"""Sidewinder: row by row, grow a horizontal run; close it by linking a random run
member to a random neighbor in the previous row.

The first row (no previous-row neighbors) becomes a single corridor. A cell with no
previous-row neighbors never closes a run early; run members with several previous-row
neighbors choose one at random. Reference: Buck, MfP ch.2.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait
from mazerunner.generators.base import Generator


@generators.register(
    "sidewinder", title="Sidewinder", requires=(Trait.ROWS,), phase=Phase.MVP,
    implemented=True, tags=(), reference="Buck, MfP ch.2",
)
class Sidewinder(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        tr = self.tracer
        for row in topo.rows():
            up: list[tuple] = []  # run members that have previous-row neighbors
            for cell in row:
                if tr.enabled:
                    tr.emit("current", cell)
                prevs = topo.prev_row_neighbors(cell)
                if prevs:
                    up.append((cell, prevs))
                nxt = topo.next_in_row(cell)
                close = nxt is None or (bool(prevs) and rng.random() < 0.5)
                if close:
                    if up:
                        member, ps = up[rng.randrange(len(up))]
                        maze.link(member, ps[rng.randrange(len(ps))])
                    up = []
                    self.bump("runs")
                else:
                    maze.link(cell, nxt)
