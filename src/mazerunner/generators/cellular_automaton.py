"""Cellular automaton "Maze" rule B3/S12345 (Pullen, Think Labyrinth). NOT a perfect maze.

Mapping to passages: the cell grid (coordinates recovered by walking axis_neighbor from the
first cell) is seeded randomly with live cells (probability `fill`, default 0.45) and the
Moore-neighborhood life rule B3/S12345 is run for `generations` steps (default 12; cells
outside the grid are dead). Live cells are "open"; every pair of orthogonally adjacent
open cells is linked. Dead cells stay isolated, so the result may have loops and
unreachable cells; solvers must cope.
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait
from mazerunner.generators.base import Generator

_STEP = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}


@generators.register(
    "cellular-automaton", title="Cellular automaton (Maze B3/S12345)", requires=(Trait.ORTHOGONAL,),
    phase=Phase.PLACEHOLDER, implemented=True, tags=('non-perfect',), reference="Pullen, Think Labyrinth",
)
class CellularAutomaton(Generator):
    produces_perfect = False

    def __init__(self, generations: int = 12, fill: float = 0.45, **params) -> None:
        super().__init__(generations=generations, fill=fill, **params)
        self.generations, self.fill = generations, fill

    def carve(self, maze: Maze, rng: random.Random) -> None:
        topo = maze.topology
        cells = topo.cell_list
        if not cells:
            return
        # coordinates by flood fill over axis_neighbor
        pos = {cells[0]: (0, 0)}
        todo = [cells[0]]
        while todo:
            c = todo.pop()
            r, q = pos[c]
            for d, (dr, dq) in _STEP.items():
                n = topo.axis_neighbor(c, d)
                if n is not None and n not in pos:
                    pos[n] = (r + dr, q + dq)
                    todo.append(n)
        at = {p: c for c, p in pos.items()}
        coords = [pos[c] for c in cells if c in pos]
        alive = {p: rng.random() < self.fill for p in coords}
        offsets = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0)]
        for _ in range(self.generations):
            new = {}
            for (r, q), live in alive.items():
                k = sum(alive.get((r + a, q + b), False) for a, b in offsets)
                new[(r, q)] = (1 <= k <= 5) if live else (k == 3)
            alive = new
            self.bump("generations")
        for p in coords:
            if alive[p]:
                for d in ("E", "S"):
                    dr, dq = _STEP[d]
                    q2 = (p[0] + dr, p[1] + dq)
                    if alive.get(q2) and topo.axis_neighbor(at[p], d) == at[q2]:
                        maze.link(at[p], at[q2])
