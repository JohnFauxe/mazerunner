"""Weighted mazes (planned, build in phase 4; PLAN §2.8).

Per-cell traversal cost (terrain). Once present, Dijkstra/A* diverge from BFS
and 'optimal' means cheapest rather than shortest.

Planned weight sources: uniform (default, = unweighted), random(lo, hi),
noise field (Perlin/value noise), image/mask, hand-authored "rooms".
Config:  [weights]  source = "random"  lo = 1  hi = 9
"""

from mazerunner.core.maze import Maze


def apply(maze: Maze, source: str = "uniform", **opts) -> None:
    raise NotImplementedError("weights: phase 4")
