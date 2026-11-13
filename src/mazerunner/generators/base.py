"""Generator interface."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import ClassVar

from mazerunner.core.maze import Maze
from mazerunner.core.endpoints import DEFAULT, place
from mazerunner.core.topology import Topology
from mazerunner.core.trace import NULL, Tracer


class Generator(ABC):
    key: ClassVar[str]
    produces_perfect: ClassVar[bool] = True  # validated by the bench runner

    def __init__(self, **params) -> None:
        self.params = params
        self.counters: dict[str, int] = {}  # algorithm-specific (e.g. walk_steps)

    @abstractmethod
    def carve(self, maze: Maze, rng: random.Random) -> None:
        """Add links to `maze` (all walls present at start).
        Wall-adding algorithms (Recursive Division) override `generate` instead."""

    def generate(self, topology: Topology, rng: random.Random, *, tracer: Tracer = NULL,
                 endpoints: dict | None = None) -> Maze:
        """Carve, then place start/goal (default: opposite sides; see core/endpoints.py)."""
        maze = Maze(topology, tracer=tracer)
        self.tracer = tracer  # for non-link events (frontier_add, walk, …)
        self.carve(maze, rng)
        ep = dict(endpoints or {})
        place(maze, ep.pop("placement", DEFAULT), rng, **ep)
        maze.meta.update(generator=self.key, params=self.params, counters=self.counters)
        return maze

    def bump(self, counter: str, n: int = 1) -> None:
        self.counters[counter] = self.counters.get(counter, 0) + n
