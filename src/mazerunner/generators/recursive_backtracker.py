"""Recursive Backtracker (randomized depth-first search), explicit stack.

Start at a random cell; repeatedly carve to a random unvisited neighbor and push it;
when stuck, pop. Reference: Buck, MfP ch.5. Notes: docs/algorithms/generation.md
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "recursive-backtracker", title="Recursive Backtracker (randomized DFS)", requires=(), phase=Phase.MVP,
    implemented=True, tags=(), reference="Buck, Mazes for Programmers ch.5",
)
class RecursiveBacktracker(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        cells = topo.cell_list
        if not cells:
            return
        tr = self.tracer
        start = cells[rng.randrange(len(cells))]
        visited = {start}
        stack = [start]
        if tr.enabled:
            tr.emit("frontier_add", start)
        while stack:
            cur = stack[-1]
            if tr.enabled:
                tr.emit("current", cur)
            options = [n for n in topo.neighbors(cur) if n not in visited]
            if options:
                nxt = options[rng.randrange(len(options))]
                maze.link(cur, nxt)
                visited.add(nxt)
                stack.append(nxt)
                if tr.enabled:
                    tr.emit("frontier_add", nxt)
            else:
                stack.pop()
                self.bump("backtracks")
                if tr.enabled:
                    tr.emit("frontier_remove", cur)
