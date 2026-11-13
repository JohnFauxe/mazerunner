"""Texture metrics computed on a generated maze (PLAN §3.1).

Every metric needs only the Maze/Topology contract; those that need a topology
trait (HEADINGS for directional bias, METRIC for tortuosity) are skipped by
`texture()` when the trait is absent.
"""

from __future__ import annotations

import math
from collections import Counter

from mazerunner.core.maze import Maze
from mazerunner.core.traits import Trait


def degree_histogram(maze: Maze) -> Counter:
    return Counter(len(maze.passages(c)) for c in maze.topology.cells())


def dead_end_ratio(maze: Maze) -> float:
    h = degree_histogram(maze)
    return h.get(1, 0) / max(1, len(maze.topology))


def diameter(maze: Maze) -> tuple[int, object, object]:
    """(length, a, b) of the longest shortest path. Two BFS sweeps: exact on
    trees (perfect mazes), a lower bound on braided mazes."""
    first = maze.topology.cell_list[0]
    d0 = maze.bfs_distances(first)
    a = max(d0, key=d0.get)
    d1 = maze.bfs_distances(a)
    b = max(d1, key=d1.get)
    return d1[b], a, b


def junction_counts(maze: Maze) -> dict[int, int]:
    """Number of cells of each passage degree, keyed by degree (1 = dead end,
    2 = corridor cell, 3 = T-junction, 4 = crossroads, ...). Sorted by degree."""
    return dict(sorted(degree_histogram(maze).items()))


def mean_corridor_length(maze: Maze) -> float:
    """Average length, in cells, of maximal corridors.

    A corridor is a connected component of the subgraph induced (via links) by
    the cells of degree exactly 2; its length is its number of cells. Dead ends
    and junctions are not part of any corridor, so a straight line of n cells
    has one corridor of length n - 2. Returns 0.0 when there are no degree-2
    cells. Long values mean long "rivers" (e.g. recursive backtracker).
    """
    two = {c for c in maze.topology.cells() if maze.degree(c) == 2}
    seen: set = set()
    lengths = []
    for c in two:
        if c in seen:
            continue
        seen.add(c)
        stack, size = [c], 0
        while stack:
            x = stack.pop()
            size += 1
            for n in maze.passages(x):
                if n in two and n not in seen:
                    seen.add(n)
                    stack.append(n)
        lengths.append(size)
    return sum(lengths) / len(lengths) if lengths else 0.0


_ORTHO_NAMES = {0: "E", 1: "N", 2: "W", 3: "S"}


def _bucket_count(maze: Maze) -> int:
    if maze.topology.has(Trait.ORTHOGONAL):
        return 4
    top = max((len(maze.topology.neighbors(c)) for c in maze.topology.cells()), default=0)
    return 6 if top <= 6 else 8


def directional_bias(maze: Maze) -> dict[str, float]:
    """Share of passage directions per heading bucket (requires HEADINGS).

    Each link counts once in each direction (a->b and b->a), so shares sum to 1
    and opposite buckets are equal by construction (E=W, N=S). Headings are
    rounded to the nearest of k equal sectors centred on 0 rad: k = 4 for
    orthogonal topologies (keys "E","N","W","S"), else 6 (hex-like, max degree
    <= 6) or 8; those keys are the sector centre in degrees ("0","60",...).
    Empty mazes give all zeros.
    """
    if not maze.topology.has(Trait.HEADINGS):
        raise NotImplementedError("directional_bias needs Trait.HEADINGS")
    k = _bucket_count(maze)
    counts = [0] * k
    for e in maze.links:
        a, b = tuple(e)
        for s, d in ((a, b), (b, a)):
            h = maze.topology.heading(s, d) % (2 * math.pi)
            counts[round(h / (2 * math.pi / k)) % k] += 1
    total = sum(counts) or 1
    if k == 4:
        keys = [_ORTHO_NAMES[i] for i in range(4)]
    else:
        keys = [f"{360 / k * i:g}" for i in range(k)]
    return {key: c / total for key, c in zip(keys, counts)}


def tortuosity(maze: Maze) -> float | None:
    """Solution length (steps, BFS ground truth) / topology.distance(start, goal).
    None if endpoints are unset, unreachable, or coincide (distance 0).
    Requires METRIC."""
    if maze.start is None or maze.goal is None:
        return None
    d = maze.topology.distance(maze.start, maze.goal)
    sol = maze.shortest_path_length()
    if not d or sol is None:
        return None
    return sol / d


def texture(maze: Maze) -> dict:
    """All applicable texture metrics as a flat, JSON-able dict.

    Keys: perfect, n_cells, n_links, diameter, dead_end_ratio, deg_<k> (cell
    count per degree), mean_corridor_length, bias_<bucket> (HEADINGS),
    solution_len / tortuosity (METRIC + endpoints; tortuosity may be None).
    """
    topo = maze.topology
    out: dict = {
        "perfect": maze.is_perfect(),
        "n_cells": len(topo),
        "n_links": maze.n_links,
        "diameter": diameter(maze)[0],
        "dead_end_ratio": dead_end_ratio(maze),
        "mean_corridor_length": mean_corridor_length(maze),
    }
    for deg, n in junction_counts(maze).items():
        out[f"deg_{deg}"] = n
    if topo.has(Trait.HEADINGS):
        for key, share in directional_bias(maze).items():
            out[f"bias_{key}"] = share
    if topo.has(Trait.METRIC) and maze.start is not None and maze.goal is not None:
        out["solution_len"] = maze.shortest_path_length()
        out["tortuosity"] = tortuosity(maze)
    return out
