"""Recursive Division (wall adding): start fully open (maze.link_all()), then split each
rectangular region with a wall that has one random gap, using an explicit stack of
regions (no recursion). Walls are built with maze.unlink() ("uncarve" events).
Regions one cell wide or tall are left open. The grid is recovered from
axis_neighbor() (row-major from the first cell), so no cell-label format is assumed.

Reference: Buck, MfP ch.12.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait
from mazerunner.generators.base import Generator


@generators.register(
    "recursive-division", title="Recursive Division", requires=(Trait.RECTANGULAR,), phase=Phase.ANALYSIS,
    implemented=True, tags=('wall-adding',), reference="Buck, MfP ch.12",
)
class RecursiveDivision(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        if not len(topo):
            return
        grid = []
        row_head = topo.cell_list[0]
        while row_head is not None:
            row, c = [], row_head
            while c is not None:
                row.append(c)
                c = topo.axis_neighbor(c, "E")
            grid.append(row)
            row_head = topo.axis_neighbor(row_head, "S")
        R, C = len(grid), len(grid[0])
        maze.link_all()
        tr = self.tracer
        stack = [(0, 0, R, C)]  # r0, c0, height, width
        while stack:
            r0, c0, h, w = stack.pop()
            if h <= 1 or w <= 1:
                continue
            self.bump("divisions")
            horizontal = h > w or (h == w and rng.random() < 0.5)
            if horizontal:
                wr = r0 + rng.randrange(h - 1)  # wall between rows wr and wr+1
                gap = c0 + rng.randrange(w)
                for c in range(c0, c0 + w):
                    if c != gap:
                        maze.unlink(grid[wr][c], grid[wr + 1][c])
                stack.append((r0, c0, wr - r0 + 1, w))
                stack.append((wr + 1, c0, r0 + h - wr - 1, w))
            else:
                wc = c0 + rng.randrange(w - 1)
                gap = r0 + rng.randrange(h)
                for r in range(r0, r0 + h):
                    if r != gap:
                        maze.unlink(grid[r][wc], grid[r][wc + 1])
                stack.append((r0, c0, h, wc - c0 + 1))
                stack.append((r0, wc + 1, h, c0 + w - wc - 1))
            if tr.enabled:
                tr.emit("current", grid[r0][c0])
