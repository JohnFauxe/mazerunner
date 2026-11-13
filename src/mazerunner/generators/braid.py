"""Braiding post-process: remove a fraction of dead ends to create loops.

Reference: Buck, MfP ch.9. Placeholder (phase 4). Applied after any generator
via the bench matrix's `braid` dimension.
"""
import random

from mazerunner.core.maze import Maze


def braid(maze: Maze, p: float, rng: random.Random) -> Maze:
    raise NotImplementedError("braid: phase 4")
