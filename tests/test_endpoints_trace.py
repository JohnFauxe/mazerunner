import random
from collections.abc import Sequence

from mazerunner.core.endpoints import opposite_sides, place
from mazerunner.core.maze import Maze
from mazerunner.core.topology import Topology
from mazerunner.core.trace import Recorder


class Ring(Topology):
    """Tiny test topology: n cells in a cycle, all on the boundary."""
    name = "ring"

    def __init__(self, n): self.n = n
    def cells(self): return iter(range(self.n))
    def neighbors(self, c) -> Sequence: return [(c - 1) % self.n, (c + 1) % self.n]
    def __len__(self): return self.n
    def boundary(self): return list(range(self.n))
    def position(self, c): return (float(c), 0.0)
    def geometry(self): return {"width": self.n, "height": 1, "cells": [], "walls": []}


def test_opposite_sides_is_half_perimeter_apart():
    a, b = opposite_sides(list(range(40)))
    assert (a, b) == (0, 20)
    a, b = opposite_sides(list(range(40)), side=0.25)
    assert (a, b) == (10, 30)


def test_place_defaults_to_opposite_sides():
    m = Maze(Ring(10))
    place(m)
    assert (m.start, m.goal) == (0, 5)
    assert m.meta["endpoints"]["placement"] == "opposite-sides"


def test_random_along_is_seeded():
    b = list(range(80))
    r1 = opposite_sides(b, along="random", rng=random.Random(1))
    r2 = opposite_sides(b, along="random", rng=random.Random(1))
    assert r1 == r2


def test_link_emits_carve_events():
    t = Ring(4)
    rec = Recorder(t.index)
    m = Maze(t, tracer=rec)
    m.link(0, 1)
    assert rec.events[0] == [0, "carve", [0, 1]]
