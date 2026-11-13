"""Generator interface.

Implementations carve passages into a Maze that starts with every wall up,
using only the Topology contract (core/topology.py) plus the trait hooks they
declare in `requires`. Use `maze.link(a, b)` (traced automatically) and
`self.tracer.emit(...)` for extra events (current, frontier_add, walk, …).
Count algorithm-specific work with `self.bump("walk_steps")`.

Start/goal placement and braiding are applied afterwards by mazerunner.api.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import ClassVar

from mazerunner.core.maze import Maze
from mazerunner.core.topology import Topology
from mazerunner.core.trace import NULL, Tracer


class Generator(ABC):
    key: ClassVar[str]
    produces_perfect: ClassVar[bool] = True  # validated by the bench runner

    def __init__(self, **params) -> None:
        self.params = params
        self.counters: dict[str, int] = {}
        self.tracer: Tracer = NULL

    @abstractmethod
    def carve(self, maze: Maze, rng: random.Random) -> None:
        """Add links to `maze` (all walls present at start). Wall-adding
        algorithms call maze.link_all() first, then maze.unlink()."""

    def generate(self, topology: Topology, rng: random.Random, *, tracer: Tracer = NULL) -> Maze:
        maze = Maze(topology, tracer=tracer)
        self.tracer = tracer
        self.counters = {}
        self.carve(maze, rng)
        maze.meta.update(generator=self.key, params=self.params, counters=dict(self.counters))
        return maze

    def bump(self, counter: str, n: int = 1) -> None:
        self.counters[counter] = self.counters.get(counter, 0) + n
