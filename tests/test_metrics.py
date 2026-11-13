import math
import random

import pytest

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators, load_all
from mazerunner.generators.base import Generator
from mazerunner.metrics import structure, uniformity
from mazerunner.metrics.solve import solve_metrics
from mazerunner.solvers.base import Outcome, SolveResult
from mazerunner.topologies.square import SquareGrid

load_all()

if "_t-dfs" not in generators:
    @generators.register("_t-dfs", title="test dfs", phase=Phase.MVP, implemented=True)
    class _TestDFS(Generator):
        def carve(self, maze, rng):
            topo = maze.topology
            start = topo.cell_list[0]
            seen, stack = {start}, [start]
            while stack:
                c = stack[-1]
                nxt = [n for n in topo.neighbors(c) if n not in seen]
                if not nxt:
                    stack.pop()
                    continue
                n = rng.choice(nxt)
                maze.link(c, n)
                seen.add(n)
                stack.append(n)

if "_t-ab" not in generators:
    @generators.register("_t-ab", title="test aldous-broder", phase=Phase.MVP, implemented=True)
    class _TestAB(Generator):
        def carve(self, maze, rng):
            topo = maze.topology
            c = rng.choice(topo.cell_list)
            seen = {c}
            while len(seen) < len(topo):
                n = rng.choice(list(topo.neighbors(c)))
                if n not in seen:
                    maze.link(c, n)
                    seen.add(n)
                c = n


def _line(n=5):
    m = Maze(SquareGrid(1, n))
    for c in range(n - 1):
        m.link((0, c), (0, c + 1))
    m.start, m.goal = (0, 0), (0, n - 1)
    return m


def _plus():
    m = Maze(SquareGrid(3, 3))
    for n in [(0, 1), (1, 0), (1, 2), (2, 1)]:
        m.link((1, 1), n)
    m.start, m.goal = (0, 1), (2, 1)
    return m


def test_corridor_metrics():
    m = _line()
    assert structure.degree_histogram(m) == {1: 2, 2: 3}
    assert structure.dead_end_ratio(m) == pytest.approx(0.4)
    assert structure.diameter(m)[0] == 4
    assert structure.mean_corridor_length(m) == 3
    assert structure.directional_bias(m) == {"E": 0.5, "N": 0.0, "W": 0.5, "S": 0.0}
    assert structure.tortuosity(m) == 1.0
    t = structure.texture(m)
    assert t["perfect"] is True and t["n_cells"] == 5 and t["n_links"] == 4
    assert t["diameter"] == 4 and t["deg_2"] == 3 and t["tortuosity"] == 1.0


def test_plus_metrics():
    m = _plus()
    assert structure.junction_counts(m) == {0: 4, 1: 4, 4: 1}
    assert structure.mean_corridor_length(m) == 0.0
    assert all(v == 0.25 for v in structure.directional_bias(m).values())
    assert structure.tortuosity(m) == 1.0  # 2 steps / manhattan 2
    t = structure.texture(m)
    assert t["perfect"] is False and t["deg_4"] == 1 and t["bias_N"] == 0.25


def test_two_corridors_mean():
    # 1x7 line with an extra spur: cells 0..6, spur from 3 to (1,3)
    m = Maze(SquareGrid(2, 7))
    for c in range(6):
        m.link((0, c), (0, c + 1))
    m.link((0, 3), (1, 3))
    # degree-2 cells: 1,2 (left corridor) and 4,5 (right corridor) -> mean 2
    assert structure.mean_corridor_length(m) == 2.0


def test_tortuosity_none_when_distance_zero():
    m = _line()
    m.goal = m.start
    assert structure.tortuosity(m) is None


def test_tortuosity_detour():
    m = Maze(SquareGrid(2, 2))
    m.link((0, 0), (1, 0)); m.link((1, 0), (1, 1)); m.link((1, 1), (0, 1))
    m.start, m.goal = (0, 0), (0, 1)
    assert structure.tortuosity(m) == 3.0


def test_spanning_tree_counts():
    for r, c, n in [(2, 2, 4), (2, 3, 15), (3, 3, 192)]:
        trees = uniformity.spanning_trees(SquareGrid(r, c))
        assert len(trees) == n == len(set(trees))
        assert all(len(t) == r * c - 1 for t in trees)


def test_chi2_survival_known_values():
    assert uniformity.chi2_sf(0, 5) == 1.0
    assert uniformity.chi2_sf(3.841459, 1) == pytest.approx(0.05, abs=1e-5)
    assert uniformity.chi2_sf(5.991465, 2) == pytest.approx(0.05, abs=1e-5)
    assert uniformity.chi2_sf(4.0, 2) == pytest.approx(math.exp(-2), rel=1e-10)
    assert uniformity.chi2_sf(18.307038, 10) == pytest.approx(0.05, abs=1e-5)
    assert uniformity.chi2_sf(191, 191) == pytest.approx(0.48639, abs=1e-4)  # near median
    assert uniformity.chi2_sf(300, 191) == pytest.approx(7.7896e-7, rel=1e-4)  # continued fraction branch
    assert uniformity.chi2_sf(1000, 3) < 1e-100


def test_chi_squared_uniform_generator_passes():
    r = uniformity.chi_squared("_t-ab", SquareGrid(2, 2), samples=800, seed=3)
    assert set(r) == {"trees", "samples", "chi2", "dof", "p_value", "unseen"}
    assert r["trees"] == 4 and r["dof"] == 3 and r["unseen"] == 0
    assert r["p_value"] > 0.001
    r = uniformity.chi_squared("_t-ab", SquareGrid(2, 3), samples=1500, seed=3)
    assert r["trees"] == 15 and r["p_value"] > 0.001


def test_chi_squared_biased_generator_fails():
    # DFS from a fixed corner on a 2x2 can only produce 2 of the 4 trees
    r = uniformity.chi_squared("_t-dfs", SquareGrid(2, 2), samples=400, seed=1)
    assert r["unseen"] == 2 and r["p_value"] < 1e-6


def test_chi_squared_deterministic():
    a = uniformity.chi_squared("_t-ab", SquareGrid(2, 2), samples=50, seed=9)
    b = uniformity.chi_squared("_t-ab", SquareGrid(2, 2), samples=50, seed=9)
    assert a == b


def test_solve_metrics():
    m = _line()
    path = [(0, c) for c in range(5)]
    d = solve_metrics(m, SolveResult(Outcome.SOLVED, path, {"nodes_expanded": 5}))
    assert d == {"outcome": "solved", "path_len": 5, "steps": 4, "optimal_len": 4,
                 "optimality": 1.0, "valid": True, "counters": {"nodes_expanded": 5}}
    # agent trail with a revisit is still valid, optimality < 1
    trail = [(0, 0), (0, 1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
    d = solve_metrics(m, SolveResult(Outcome.SOLVED, trail, {}))
    assert d["valid"] and d["steps"] == 6 and d["optimality"] == pytest.approx(4 / 6)
    # failed run: no optimality; teleporting path invalid
    d = solve_metrics(m, SolveResult(Outcome.TIMEOUT, trail[:3], {}))
    assert d["optimality"] is None and d["outcome"] == "timeout" and not d["valid"]
    bad = solve_metrics(m, SolveResult(Outcome.SOLVED, [(0, 0), (0, 4)], {}))
    assert bad["valid"] is False
