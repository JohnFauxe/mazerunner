"""Braiding post-process: remove a fraction of dead ends to create loops.

Reference: Buck, MfP ch.9. For each dead end (shuffled order), with probability p link it
to an unlinked neighbor, preferring a neighbor that is itself a dead end. Applied after
any generator via the api / bench matrix's `braid` dimension.
"""
import random

from mazerunner.core.maze import Maze


def braid(maze: Maze, p: float, rng: random.Random) -> Maze:
    if p <= 0:
        return maze
    topo = maze.topology
    dead_ends = [c for c in topo.cell_list if maze.degree(c) == 1]
    rng.shuffle(dead_ends)
    for cell in dead_ends:
        if maze.degree(cell) != 1 or rng.random() >= p:
            continue
        unlinked = [n for n in topo.neighbors(cell) if not maze.linked(cell, n)]
        if not unlinked:
            continue
        best = [n for n in unlinked if maze.degree(n) == 1] or unlinked
        maze.link(cell, best[rng.randrange(len(best))])
    return maze
