"""Growing Tree: keep a list of active cells; pick one by a strategy; carve to a random
unvisited neighbor (it becomes active) or retire the cell.

Params: strategy in {"newest" (DFS-like), "random" (Prim-like), "oldest", "middle",
"mix"}; mix = probability of choosing newest when strategy == "mix" (default 0.5,
otherwise random). Reference: Buck blog 2011; MfP ch.11.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator

STRATEGIES = ("newest", "random", "oldest", "middle", "mix")


@generators.register(
    "growing-tree", title="Growing Tree", requires=(), phase=Phase.ROUND_HEX,
    implemented=True, tags=('tunable',), reference="Buck blog 2011; MfP ch.11",
)
class GrowingTree(Generator):

    def __init__(self, strategy: str = "newest", mix: float = 0.5, **params) -> None:
        if strategy not in STRATEGIES:
            raise ValueError(f"unknown growing-tree strategy {strategy!r}; expected one of {STRATEGIES}")
        super().__init__(strategy=strategy, mix=mix, **params)
        self.strategy, self.mix = strategy, mix

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        cells = topo.cell_list
        if not cells:
            return
        tr = self.tracer
        strategy, mix = self.strategy, self.mix
        start = cells[rng.randrange(len(cells))]
        visited = {start}
        active = [start]
        if tr.enabled:
            tr.emit("frontier_add", start)
        while active:
            last = len(active) - 1
            if strategy == "newest":
                i = last
            elif strategy == "random":
                i = rng.randrange(len(active))
            elif strategy == "oldest":
                i = 0
            elif strategy == "middle":
                i = len(active) // 2
            else:
                i = last if rng.random() < mix else rng.randrange(len(active))
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
                if i == last:
                    active.pop()
                elif strategy == "random":
                    active[i] = active.pop()
                else:
                    del active[i]
                if tr.enabled:
                    tr.emit("frontier_remove", cur)
