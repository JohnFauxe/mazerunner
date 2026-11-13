"""Prim's (simplified): keep a set of active cells; pick one at random; carve to a random
unvisited neighbor (which becomes active) or retire the cell when it has none.

Reference: Prim 1957; Buck, MfP ch.11 (simplified Prim).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "prim-simplified", title="Prim's (simplified)", requires=(), phase=Phase.ROUND_HEX,
    implemented=True, tags=(), reference="Prim 1957; Buck, MfP ch.11",
)
class PrimSimplified(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        cells = topo.cell_list
        if not cells:
            return
        tr = self.tracer
        start = cells[rng.randrange(len(cells))]
        visited = {start}
        active = [start]
        if tr.enabled:
            tr.emit("frontier_add", start)
        while active:
            i = rng.randrange(len(active))
            cur = active[i]
            if tr.enabled:
                tr.emit("current", cur)
            options = [x for x in topo.neighbors(cur) if x not in visited]
            if options:
                nxt = options[rng.randrange(len(options))]
                maze.link(cur, nxt)
                visited.add(nxt)
                active.append(nxt)
                if tr.enabled:
                    tr.emit("frontier_add", nxt)
            else:
                last = active.pop()
                if i < len(active):
                    active[i] = last
                if tr.enabled:
                    tr.emit("frontier_remove", cur)
