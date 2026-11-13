"""Eller's algorithm: one row at a time with set (connectivity) bookkeeping.

For each row: randomly merge adjacent cells of different sets (always, in the last row);
then every set links down through at least one random member (others with probability
1/3) to a random neighbor in the next row. Works for rows whose cells have 0..n
next-row neighbors: a downward link to a next-row cell already connected to this set is
skipped (it would form a loop) and linking to a different set merges the two.
Sets are a union-find keyed by cell. Reference: Eller 1982; Buck, MfP ch.12.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait
from mazerunner.generators.base import Generator


@generators.register(
    "eller", title="Eller's", requires=(Trait.ROWS,), phase=Phase.ANALYSIS,
    implemented=True, tags=('streaming',), reference="Eller 1982; Pullen, Think Labyrinth",
)
class Eller(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        tr = self.tracer
        rows = topo.rows()
        parent: dict = {}

        def find(c):
            root = parent.setdefault(c, c)
            while parent[root] != root:
                root = parent[root]
            while parent[c] != root:  # path compression
                parent[c], c = root, parent[c]
            return root

        def union(a, b) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        last_row = len(rows) - 1
        for ri, row in enumerate(rows):
            final = ri == last_row
            # 1. horizontal merges
            for cell in row:
                if tr.enabled:
                    tr.emit("current", cell)
                nxt = topo.next_in_row(cell)
                if nxt is None or find(cell) == find(nxt):
                    continue
                if final or rng.random() < 0.5:
                    maze.link(cell, nxt)
                    union(cell, nxt)
                    if tr.enabled:
                        tr.emit("set_merge", cell, nxt)
            if final:
                break
            # 2. vertical links: each set drops down at least once
            groups: dict = {}
            for cell in row:
                groups.setdefault(find(cell), []).append(cell)
            for members in groups.values():
                rng.shuffle(members)
                made = False
                for cell in members:
                    if made and rng.random() >= 1 / 3:
                        continue
                    downs = [d for d in topo.next_row_neighbors(cell) if find(d) != find(cell)]
                    if not downs:
                        continue
                    d = downs[rng.randrange(len(downs))]
                    maze.link(cell, d)
                    union(cell, d)
                    made = True
                    if tr.enabled:
                        tr.emit("set_merge", cell, d)
