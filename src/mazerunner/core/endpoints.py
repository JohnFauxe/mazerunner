"""Start/goal placement, chosen at generation time (PLAN §2.7).

Config (benchmarks/configs/*.toml or CLI flags):

    [endpoints]
    placement = "opposite-sides"   # default
    along     = "center"           # "center" | "random": position along the side
    side      = 0.0                # which pair of sides, as a fraction of the boundary
                                   # (square: 0.0 = west→east, 0.25 = north→south)
    # placement = "manual" → start = [r, c], goal = [r, c]
"""

from __future__ import annotations

import random
from enum import Enum

from mazerunner.core.maze import Maze
from mazerunner.core.topology import Cell


class Placement(str, Enum):
    OPPOSITE_SIDES = "opposite-sides"  # default: generic via Topology.boundary()
    CORNERS = "corners"                # first/last cell (square: NW→SE)
    DIAMETER = "diameter"              # longest shortest path; needs carved maze
    CENTER_OUT = "center-out"          # centre → boundary (natural for polar)
    RANDOM = "random"
    MANUAL = "manual"


DEFAULT = Placement.OPPOSITE_SIDES


def opposite_sides(boundary: list[Cell], *, side: float = 0.0, along: str = "center",
                   rng: random.Random | None = None) -> tuple[Cell, Cell]:
    """Pick two boundary cells half a perimeter apart.

    `boundary` is the topology's boundary cells in cyclic order, starting at the
    middle of its first side. That gives: square → middle of west edge vs middle
    of east edge, polar → two antipodal outer-ring cells, hex → opposite edges.
    """
    n = len(boundary)
    i = int(side * n) % n
    if along == "random":
        if rng is None:
            raise ValueError("along='random' needs an rng")
        # jitter within ±1/8 perimeter so the points stay on the same sides
        i = (i + rng.randint(-n // 8, n // 8)) % n
    return boundary[i], boundary[(i + n // 2) % n]


def place(maze: Maze, placement: Placement | str = DEFAULT, rng: random.Random | None = None,
          **opts) -> None:
    """Set maze.start / maze.goal. Run after carving (DIAMETER needs the links)."""
    p = Placement(placement)
    topo = maze.topology
    if p is Placement.OPPOSITE_SIDES:
        maze.start, maze.goal = opposite_sides(topo.boundary(), rng=rng, **opts)
    elif p is Placement.CORNERS:
        maze.start, maze.goal = topo.default_endpoints()
    elif p is Placement.MANUAL:
        maze.start, maze.goal = tuple(opts["start"]), tuple(opts["goal"])
    elif p is Placement.RANDOM:
        a, b = (rng or random.Random()).sample(list(topo.cells()), 2)
        maze.start, maze.goal = a, b
    else:  # DIAMETER, CENTER_OUT
        raise NotImplementedError(f"placement {p.value}: phase 1/2")
    maze.meta["endpoints"] = {"placement": p.value, **{k: v for k, v in opts.items()}}
