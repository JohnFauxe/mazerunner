"""Hunt-and-Kill: random walk (kill) until stuck, then scan cells in order for an
unvisited cell adjacent to the maze (hunt) and link it to a random visited neighbor.

Reference: Buck, MfP ch.5. Notes: docs/algorithms/generation.md
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "hunt-and-kill", title="Hunt-and-Kill", requires=(), phase=Phase.ROUND_HEX,
    implemented=True, tags=(), reference="Buck, MfP ch.5",
)
class HuntAndKill(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        cells = topo.cell_list
        n = len(cells)
        if not n:
            return
        tr = self.tracer
        cur = cells[rng.randrange(n)]
        visited = {cur}
        first_unvisited = 0  # every cell before this index is visited (valid scan start)
        while True:
            if tr.enabled:
                tr.emit("current", cur)
            options = [x for x in topo.neighbors(cur) if x not in visited]
            if options:
                nxt = options[rng.randrange(len(options))]
                maze.link(cur, nxt)
                visited.add(nxt)
                cur = nxt
                continue
            # hunt
            self.bump("hunts")
            found = None
            i = first_unvisited
            while i < n and cells[i] in visited:
                i += 1
            first_unvisited = i
            while i < n:
                c = cells[i]
                i += 1
                if c in visited:
                    continue
                if tr.enabled:
                    tr.emit("current", c)
                vn = [x for x in topo.neighbors(c) if x in visited]
                self.bump("hunt_steps")
                if vn:
                    found = (c, vn[rng.randrange(len(vn))])
                    break
            if found is None:
                return
            cur, anchor = found
            maze.link(cur, anchor)
            visited.add(cur)
