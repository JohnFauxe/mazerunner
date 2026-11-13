"""Wilson's algorithm: loop-erased random walks until they hit the maze.

Uniform over spanning trees. Reference: Wilson, STOC 1996.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


def wilson_complete(gen: Generator, maze: Maze, rng: random.Random, in_tree: set) -> None:
    """Run Wilson's algorithm until every cell is in `in_tree` (mutated in place).
    `in_tree` must be non-empty (or the topology empty)."""
    topo = maze.topology
    tr = gen.tracer
    pool = [c for c in topo.cell_list if c not in in_tree]  # unvisited cells
    where = {c: i for i, c in enumerate(pool)}

    def drop(c) -> None:  # O(1) removal from the pool
        i = where.pop(c)
        last = pool.pop()
        if i < len(pool):
            pool[i] = last
            where[last] = i

    steps = 0
    while pool:
        start = pool[rng.randrange(len(pool))]
        path = [start]
        pos = {start: 0}
        cur = start
        while cur not in in_tree:
            nbrs = topo.neighbors(cur)
            nxt = nbrs[rng.randrange(len(nbrs))]
            steps += 1
            if tr.enabled:
                tr.emit("walk", cur, nxt)
            if nxt in pos:  # loop: erase back to the earlier visit
                k = pos[nxt]
                if k + 1 < len(path):
                    if tr.enabled:
                        tr.emit("erase", *path[k + 1:])
                    for c in path[k + 1:]:
                        del pos[c]
                    del path[k + 1:]
            else:
                pos[nxt] = len(path)
                path.append(nxt)
            cur = nxt
        # path is loop-free and path[-1] is already in the tree
        for a, b in zip(path, path[1:]):
            maze.link(a, b)
        for c in path[:-1]:
            in_tree.add(c)
            drop(c)
    gen.bump("walk_steps", steps)


@generators.register(
    "wilson", title="Wilson's (loop-erased random walk)", requires=(), phase=Phase.MVP,
    implemented=True, tags=('uniform',), reference="Wilson, STOC 1996",
)
class Wilson(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        cells = maze.topology.cell_list
        if not cells:
            return
        root = cells[rng.randrange(len(cells))]
        wilson_complete(self, maze, rng, {root})
