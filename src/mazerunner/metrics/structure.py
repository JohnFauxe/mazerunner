"""Texture metrics computed on a generated maze (PLAN §3.1)."""

from collections import Counter

from mazerunner.core.maze import Maze


def degree_histogram(maze: Maze) -> Counter:
    return Counter(len(maze.passages(c)) for c in maze.topology.cells())


def dead_end_ratio(maze: Maze) -> float:
    h = degree_histogram(maze)
    return h.get(1, 0) / max(1, len(maze.topology))


def diameter(maze: Maze) -> tuple[int, object, object]:
    """Longest shortest path (two BFS sweeps; exact on trees). Phase 1."""
    raise NotImplementedError


def mean_corridor_length(maze: Maze) -> float:
    """Average run length of degree-2 chains ("river" factor). Phase 3."""
    raise NotImplementedError


def directional_bias(maze: Maze) -> dict[str, float]:
    """Share of links per heading bucket. Requires HEADINGS. Phase 3."""
    raise NotImplementedError


def texture(maze: Maze) -> dict:
    """All implemented texture metrics as a flat dict for the results row."""
    return {
        "dead_end_ratio": dead_end_ratio(maze),
        "degree_hist": dict(degree_histogram(maze)),
    }
