"""Maze ⇄ JSON: {topology, args, links: [[a, b], ...], start, goal, meta}.
Lets mazes be generated once and solved many times / shared. Phase 1."""

from mazerunner.core.maze import Maze


def dumps(maze: Maze) -> str:
    raise NotImplementedError


def loads(s: str) -> Maze:
    raise NotImplementedError
