"""Maze = Topology + carved links + endpoints."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from mazerunner.core.topology import Cell, Topology
from mazerunner.core.trace import NULL, Tracer

Edge = frozenset  # frozenset({a, b})


@dataclass
class Maze:
    topology: Topology
    links: set[Edge] = field(default_factory=set)
    start: Cell | None = None
    goal: Cell | None = None
    weights: dict[Cell, float] | None = None  # planned, phase 4: weighted cells (PLAN §2.8)
    meta: dict = field(default_factory=dict)  # generator name, seed, counters…
    tracer: Tracer = field(default=NULL, repr=False, compare=False)

    # --- mutation (generators) ------------------------------------------
    def link(self, a: Cell, b: Cell) -> None:
        self.links.add(frozenset((a, b)))
        self.tracer.emit("carve", a, b)

    def unlink(self, a: Cell, b: Cell) -> None:
        self.links.discard(frozenset((a, b)))
        self.tracer.emit("uncarve", a, b)

    # --- queries (solvers / metrics) ------------------------------------
    def linked(self, a: Cell, b: Cell) -> bool:
        return frozenset((a, b)) in self.links

    def passages(self, cell: Cell) -> list[Cell]:
        """Linked neighbors, preserving the topology's (cyclic) order."""
        return [n for n in self.topology.neighbors(cell) if self.linked(cell, n)]

    # --- validation -----------------------------------------------------
    def is_connected(self) -> bool:
        cells = list(self.topology.cells())
        if not cells:
            return True
        seen = {cells[0]}
        q = deque([cells[0]])
        while q:
            for n in self.passages(q.popleft()):
                if n not in seen:
                    seen.add(n)
                    q.append(n)
        return len(seen) == len(cells)

    def is_perfect(self) -> bool:
        """Spanning tree ⇔ connected and |E| = |V| − 1."""
        return len(self.links) == len(self.topology) - 1 and self.is_connected()

    def verify_path(self, path: list[Cell]) -> bool:
        if not path or path[0] != self.start or path[-1] != self.goal:
            return False
        return all(self.linked(a, b) for a, b in zip(path, path[1:]))
