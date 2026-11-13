"""Prim's (true, random weights): give every cell a random cost, then grow the tree by
always extending from the cheapest active cell to its cheapest unvisited neighbor
(priority queue). Retire a cell once it has no unvisited neighbors.

Reference: Prim 1957; Buck, MfP ch.11 (true Prim).
"""
import heapq
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "prim-true", title="Prim's (true, random weights)", requires=(), phase=Phase.ROUND_HEX,
    implemented=True, tags=(), reference="Prim 1957; Buck, MfP ch.11",
)
class PrimTrue(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        cells = topo.cell_list
        if not cells:
            return
        tr = self.tracer
        index = topo.index
        cost = [rng.random() for _ in cells]
        start = cells[rng.randrange(len(cells))]
        visited = {start}
        heap = [(cost[index[start]], index[start])]
        if tr.enabled:
            tr.emit("frontier_add", start)
        while heap:
            _, ci = heap[0]
            cur = cells[ci]
            if tr.enabled:
                tr.emit("current", cur)
            best, best_cost = None, 0.0
            for x in topo.neighbors(cur):
                if x not in visited:
                    cx = cost[index[x]]
                    if best is None or cx < best_cost:
                        best, best_cost = x, cx
            if best is None:
                heapq.heappop(heap)
                if tr.enabled:
                    tr.emit("frontier_remove", cur)
            else:
                maze.link(cur, best)
                visited.add(best)
                heapq.heappush(heap, (best_cost, index[best]))
                if tr.enabled:
                    tr.emit("frontier_add", best)
