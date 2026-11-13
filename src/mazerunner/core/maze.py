"""Maze = Topology + carved links + endpoints."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from mazerunner.core.topology import Cell, Topology
from mazerunner.core.trace import NULL, Tracer

Edge = frozenset  # frozenset({a, b})


@dataclass(eq=False)
class Maze:
    topology: Topology
    start: Cell | None = None
    goal: Cell | None = None
    weights: dict[Cell, float] | None = None  # planned, phase 4: weighted cells (PLAN §2.8)
    meta: dict = field(default_factory=dict)  # generator name, seed, counters…
    tracer: Tracer = field(default=NULL, repr=False)

    def __post_init__(self) -> None:
        self._adj: dict[Cell, set[Cell]] = {c: set() for c in self.topology.cells()}
        self._n_links = 0

    # --- mutation (generators) ------------------------------------------
    def link(self, a: Cell, b: Cell) -> None:
        if b not in self._adj[a]:
            self._adj[a].add(b)
            self._adj[b].add(a)
            self._n_links += 1
        self.tracer.emit("carve", a, b)

    def unlink(self, a: Cell, b: Cell) -> None:
        if b in self._adj[a]:
            self._adj[a].discard(b)
            self._adj[b].discard(a)
            self._n_links -= 1
        self.tracer.emit("uncarve", a, b)

    def link_all(self) -> None:
        """Open every adjacency (start state for wall-adding generators).
        Traced as a single "open_all" event."""
        for c in self.topology.cells():
            for n in self.topology.neighbors(c):
                if n not in self._adj[c]:
                    self._adj[c].add(n)
                    self._adj[n].add(c)
                    self._n_links += 1
        self.tracer.emit("open_all")

    # --- queries (solvers / metrics) ------------------------------------
    def linked(self, a: Cell, b: Cell) -> bool:
        return b in self._adj[a]

    def passages(self, cell: Cell) -> list[Cell]:
        """Linked neighbors, preserving the topology's (cyclic) order."""
        adj = self._adj[cell]
        return [n for n in self.topology.neighbors(cell) if n in adj]

    def degree(self, cell: Cell) -> int:
        return len(self._adj[cell])

    @property
    def links(self) -> set[Edge]:
        return {frozenset((a, b)) for a, ns in self._adj.items() for b in ns}

    @property
    def n_links(self) -> int:
        return self._n_links

    def cost(self, a: Cell, b: Cell) -> float:
        """Cost of stepping a→b (entering b). 1 unless weights are set."""
        return 1.0 if self.weights is None else self.weights.get(b, 1.0)

    # --- validation -----------------------------------------------------
    def bfs_distances(self, source: Cell) -> dict[Cell, int]:
        dist = {source: 0}
        q = deque([source])
        while q:
            c = q.popleft()
            for n in self._adj[c]:
                if n not in dist:
                    dist[n] = dist[c] + 1
                    q.append(n)
        return dist

    def is_connected(self) -> bool:
        cells = self.topology.cell_list
        return not cells or len(self.bfs_distances(cells[0])) == len(cells)

    def is_perfect(self) -> bool:
        """Spanning tree ⇔ connected and |E| = |V| − 1."""
        return self._n_links == len(self.topology) - 1 and self.is_connected()

    def verify_path(self, path: list[Cell]) -> bool:
        if not path or path[0] != self.start or path[-1] != self.goal:
            return False
        return all(self.linked(a, b) for a, b in zip(path, path[1:]))

    def shortest_path_length(self) -> int | None:
        """Ground truth (BFS, unweighted) for optimality ratios."""
        return self.bfs_distances(self.start).get(self.goal)
