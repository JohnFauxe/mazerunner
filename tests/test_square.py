import math

from mazerunner.core.maze import Maze
from mazerunner.core.trace import Recorder
from mazerunner.core.endpoints import place
from mazerunner.topologies.square import SquareGrid


def test_square_basics():
    g = SquareGrid(3, 4)
    assert len(g) == 12 and len(list(g.cells())) == 12
    assert g.neighbors((0, 0)) == ((0, 1), (1, 0))  # E, S (no N/W)
    assert g.neighbors((1, 1)) == ((1, 2), (0, 1), (1, 0), (2, 1))  # E N W S = CCW
    assert g.heading((1, 1), (0, 1)) == math.pi / 2


def test_boundary_opposite_sides():
    g = SquareGrid(11, 11)
    b = g.boundary()
    assert b[0] == (5, 0) and b[len(b) // 2] == (5, 10)
    m = Maze(g)
    place(m)
    assert (m.start, m.goal) == ((5, 0), (5, 10))
    place(m, side=0.25)
    assert (m.start, m.goal) == ((10, 5), (0, 5))


def test_geometry_walls_cover_every_adjacency_once():
    g = SquareGrid(4, 5)
    geo = g.geometry()
    inner = {frozenset((w["a"], w["b"])) for w in geo["walls"] if w["b"] is not None}
    expect = {frozenset((g.index[a], g.index[b])) for a in g.cells() for b in g.neighbors(a)}
    assert inner == expect
    assert len(geo["cells"]) == 20


def test_maze_links_and_trace():
    g = SquareGrid(2, 2)
    rec = Recorder(g.index)
    m = Maze(g, tracer=rec)
    m.link((0, 0), (0, 1)); m.link((0, 1), (1, 1)); m.link((1, 1), (1, 0))
    assert m.is_perfect() and m.n_links == 3
    assert m.passages((0, 1)) == [(0, 0), (1, 1)]  # topology order E,N,W,S filtered
    assert rec.events[0] == [0, "carve", [0, 1]]
