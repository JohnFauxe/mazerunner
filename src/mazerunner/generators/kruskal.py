"""Randomized Kruskal's: shuffle all edges; carve an edge when its endpoints are in
different sets (union-find with path compression and union by rank).

Reference: Kruskal 1956; Buck, MfP ch.11.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "kruskal", title="Randomized Kruskal's", requires=(), phase=Phase.ROUND_HEX,
    implemented=True, tags=(), reference="Kruskal 1956",
)
class Kruskal(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        cells = topo.cell_list
        n = len(cells)
        index = topo.index
        edges = [(i, index[x]) for i, c in enumerate(cells)
                 for x in topo.neighbors(c) if i < index[x]]
        rng.shuffle(edges)
        parent = list(range(n))
        rank = [0] * n
        tr = self.tracer
        need = n - 1
        for a, b in edges:
            if need <= 0:
                break
            ra = a
            while parent[ra] != ra:
                parent[ra] = parent[parent[ra]]
                ra = parent[ra]
            rb = b
            while parent[rb] != rb:
                parent[rb] = parent[parent[rb]]
                rb = parent[rb]
            self.bump("edges_examined")
            if ra == rb:
                continue
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1
            need -= 1
            ca, cb = cells[a], cells[b]
            maze.link(ca, cb)
            if tr.enabled:
                tr.emit("set_merge", ca, cb)
