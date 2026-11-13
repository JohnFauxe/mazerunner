"""Solver tests. Mazes are carved by a local helper so these tests are independent of generators."""
from __future__ import annotations

import math
import random

import pytest

from mazerunner.api import make_topology, solve
from mazerunner.core.maze import Maze
from mazerunner.core.registry import solvers
from mazerunner.solvers.base import Outcome
from mazerunner.topologies.square import SquareGrid

OPTIMAL = ["bfs", "dijkstra", "astar", "bidirectional-bfs", "idastar", "jps"]
NONOPT_OMNI = ["dfs", "greedy", "dead-end-filling"]
ALL_OMNI = OPTIMAL + NONOPT_OMNI
ALL_KEYS = ALL_OMNI + ["wall-follower", "random-mouse", "tremaux", "pledge", "chain"]


def carve(topo, seed: int, braid: float = 0.0, corners: bool = True) -> Maze:
    """Randomized DFS spanning tree (iterative) + `braid` fraction of extra random links."""
    rng = random.Random(seed)
    m = Maze(topo)
    cells = topo.cell_list
    seen = {cells[0]}
    stack = [cells[0]]
    while stack:
        c = stack[-1]
        nb = [n for n in topo.neighbors(c) if n not in seen]
        if not nb:
            stack.pop()
            continue
        n = rng.choice(nb)
        m.link(c, n)
        seen.add(n)
        stack.append(n)
    if braid:
        for c in cells:
            for n in topo.neighbors(c):
                if not m.linked(c, n) and rng.random() < braid:
                    m.link(c, n)
    m.start, m.goal = cells[0], cells[-1]
    return m


def sq(r, c=None, seed=0, braid=0.0):
    return carve(SquareGrid(r, c), seed, braid)


def run(maze, key, seed=0, **params):
    return solve(maze, key, seed, params=params or None)


def check_linked_trail(maze, path):
    assert all(maze.linked(a, b) for a, b in zip(path, path[1:]))


SIZES = [(1, 1), (1, 7), (7, 1), (2, 2), (5, 5), (8, 13), (15, 15)]


@pytest.mark.parametrize("key", OPTIMAL)
@pytest.mark.parametrize("braid", [0.0, 0.3])
def test_optimal_solvers(key, braid):
    for r, c in SIZES:
        for seed in range(6):
            m = sq(r, c, seed, braid)
            res = run(m, key, seed)
            assert res.outcome is Outcome.SOLVED, (key, r, c, seed)
            assert m.verify_path(res.path)
            assert len(res.path) == m.shortest_path_length() + 1
            assert res.counters["nodes_expanded"] >= 1


@pytest.mark.parametrize("key", NONOPT_OMNI)
@pytest.mark.parametrize("braid", [0.0, 0.3])
def test_nonoptimal_omniscient_valid(key, braid):
    for r, c in SIZES:
        for seed in range(6):
            m = sq(r, c, seed, braid)
            res = run(m, key, seed)
            assert res.outcome is Outcome.SOLVED, (key, r, c, seed)
            assert m.verify_path(res.path)
            if braid == 0.0:  # unique path on perfect mazes
                assert len(res.path) == m.shortest_path_length() + 1


def test_start_equals_goal():
    m = sq(1, 1)
    for key in ALL_KEYS:
        res = run(m, key)
        assert res.outcome is Outcome.SOLVED and res.path == [m.start]


def test_astar_weighted_valid_and_cheaper():
    m = sq(25, 25, 3, 0.4)
    a = run(m, "astar")
    w = run(m, "astar", heuristic_scale=3.0)
    assert m.verify_path(w.path)
    assert len(w.path) >= len(a.path)
    assert w.counters["nodes_expanded"] <= a.counters["nodes_expanded"]


def test_astar_expands_no_more_than_dijkstra():
    m = sq(20, 20, 5, 0.3)
    assert run(m, "astar").counters["nodes_expanded"] <= run(m, "dijkstra").counters["nodes_expanded"]


def test_jps_open_grid_optimal():
    m = Maze(SquareGrid(12, 12))
    m.link_all()
    m.start, m.goal = (0, 0), (11, 11)
    res = run(m, "jps")
    assert m.verify_path(res.path) and len(res.path) == 23


@pytest.mark.parametrize("key", ALL_OMNI)
def test_unreachable_goal_fails(key):
    m = Maze(SquareGrid(3, 3))
    for a, b in [((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 0), (1, 0))]:
        m.link(a, b)
    m.start, m.goal = (0, 0), (2, 2)
    res = run(m, key)
    assert res.outcome is Outcome.FAILED and res.path == []


@pytest.mark.parametrize("key", ["tremaux", "wall-follower", "chain"])
def test_agent_unreachable_goal_not_solved(key):
    m = Maze(SquareGrid(3, 3))
    for a, b in [((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 0), (1, 0))]:
        m.link(a, b)
    m.start, m.goal = (0, 0), (2, 2)
    res = run(m, key)
    assert res.outcome in (Outcome.FAILED, Outcome.TIMEOUT)


def test_idastar_phase_events_and_no_recursion():
    from mazerunner.core.trace import Recorder
    m = sq(6, 6, 1, 0.2)
    rec = Recorder(m.topology.index)
    res = solve(m, "idastar", 0, tracer=rec)
    assert res.outcome is Outcome.SOLVED
    phases = [e for e in rec.events if e[1] == "phase" and e[3]["label"].startswith("bound")]
    assert len(phases) == res.counters["iterations"] >= 1


def test_dead_end_filling_traces_fill():
    from mazerunner.core.trace import Recorder
    m = sq(8, 8, 2)
    rec = Recorder(m.topology.index)
    res = solve(m, "dead-end-filling", 0, tracer=rec)
    fills = [e for e in rec.events if e[1] == "fill"]
    assert len(fills) == res.counters["cells_filled"] > 0


def test_traced_run_matches_untraced():
    from mazerunner.core.trace import Recorder
    m = sq(9, 9, 4, 0.2)
    for key in ALL_OMNI:
        a = run(m, key)
        b = solve(m, key, 0, tracer=Recorder(m.topology.index))
        assert a.path == b.path


# ----------------------------------------------------------------- agents
BIG = {"step_budget": 10_000_000}


@pytest.mark.parametrize("hand", ["left", "right"])
def test_wall_follower_solves_perfect(hand):
    for r, c in SIZES:
        for seed in range(8):
            m = sq(r, c, seed)
            res = run(m, "wall-follower", seed, hand=hand)
            assert res.outcome is Outcome.SOLVED, (hand, r, c, seed)
            assert res.path[0] == m.start and res.path[-1] == m.goal
            check_linked_trail(m, res.path)


def test_wall_follower_hands_are_mirrors():
    # open 3x3 room: right hand and left hand must circle in opposite directions
    m = Maze(SquareGrid(3, 3))
    m.link_all()
    m.start, m.goal = (0, 0), (2, 2)
    walks = {}
    for hand in ("left", "right"):
        res = run(m, "wall-follower", 0, hand=hand)
        walks[hand] = res.path
    assert walks["left"] != walks["right"]
    # arrive at (1,1) from the south heading north: right hand must go east, left hand west
    m2 = Maze(SquareGrid(3, 3))
    m2.link_all()
    m2.start, m2.goal = (2, 1), (0, 0)
    from mazerunner.solvers.base import Probe
    from mazerunner.solvers.wall_follower import WallFollower
    for hand, expect in (("right", (1, 2)), ("left", (1, 0))):
        p = Probe(m2, 3)
        p.move((1, 1))  # arrived heading north
        s = WallFollower(hand=hand)
        # run one decision: next move after (2,1)->(1,1)
        try:
            s.run(p, random.Random(0))
        except TimeoutError:
            pass
        assert p.trail[2] == expect, (hand, p.trail)


def test_wall_follower_fails_with_loop_around_goal():
    # A loop (ring) with the goal on a stub off its inside; the start hangs off the ring outside.
    # The wall follower is attached to the outer wall of the ring and cannot enter the stub.
    m = Maze(SquareGrid(7, 7))
    ring = [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 5), (3, 5), (4, 5), (5, 5),
            (5, 4), (5, 3), (5, 2), (5, 1), (4, 1), (3, 1), (2, 1)]
    for a, b in zip(ring, ring[1:] + ring[:1]):
        m.link(a, b)
    m.link((0, 1), (1, 1))                    # start spur
    m.link((3, 3), (3, 2)); m.link((3, 2), (3, 1))  # goal reached via inner branch at (3,1)
    m.start, m.goal = (0, 1), (3, 3)
    assert run(m, "bfs").outcome is Outcome.SOLVED
    outcomes = {hand: run(m, "wall-follower", 0, hand=hand, step_budget=5000).outcome
                for hand in ("left", "right")}
    # the stub hangs on the ring's inside; the hand that hugs the outside never enters it
    assert any(o is not Outcome.SOLVED for o in outcomes.values()), outcomes


@pytest.mark.parametrize("seed", range(5))
def test_random_mouse_perfect(seed):
    for r, c in [(1, 6), (5, 5), (8, 8)]:
        m = sq(r, c, seed)
        res = run(m, "random-mouse", seed, **BIG)
        assert res.outcome is Outcome.SOLVED
        check_linked_trail(m, res.path)


def test_random_mouse_no_reversal_unless_dead_end():
    m = sq(8, 8, 1, 0.3)
    res = run(m, "random-mouse", 3, **BIG)
    t = res.path
    for a, b, c in zip(t, t[1:], t[2:]):
        if c == a:
            assert m.degree(b) == 1


def test_random_mouse_timeout():
    m = sq(10, 10, 0)
    res = run(m, "random-mouse", 0, step_budget=3)
    assert res.outcome is Outcome.TIMEOUT


@pytest.mark.parametrize("braid", [0.0, 0.2, 0.6, 1.0])
def test_tremaux_terminates_and_solves(braid):
    for r, c in [(1, 5), (6, 6), (9, 12)]:
        for seed in range(6):
            m = sq(r, c, seed, braid)
            res = run(m, "tremaux", seed)  # default budget 10n only if it were to loop
            assert res.outcome is Outcome.SOLVED, (braid, r, c, seed, res.counters)
            check_linked_trail(m, res.path)
            assert m.verify_path(res.path)


def test_tremaux_never_walks_passage_more_than_twice():
    m = sq(10, 10, 2, 0.4)
    res = run(m, "tremaux", 1)
    from collections import Counter
    cnt = Counter(frozenset(e) for e in zip(res.path, res.path[1:]))
    assert max(cnt.values()) <= 2


def test_chain_perfect():
    for r, c in [(1, 6), (6, 6), (9, 12)]:
        for seed in range(6):
            m = sq(r, c, seed)
            res = run(m, "chain", seed, **BIG)
            assert res.outcome is Outcome.SOLVED, (r, c, seed)
            check_linked_trail(m, res.path)


def test_pledge_escapes_and_stops_at_goal():
    # goal on the east border: pledge heading east walks straight out of a perfect maze eventually
    solved = 0
    for seed in range(10):
        m = sq(8, 8, seed)
        m.start, m.goal = (0, 0), (7, 7)
        res = run(m, "pledge", seed, step_budget=5000)
        assert res.outcome in (Outcome.SOLVED, Outcome.FAILED, Outcome.TIMEOUT)
        check_linked_trail(m, res.path)
        solved += res.outcome is Outcome.SOLVED
    assert solved >= 1


def test_pledge_turn_sum_logic_open_room():
    m = Maze(SquareGrid(1, 6))
    m.link_all()
    m.start, m.goal = (0, 0), (0, 5)
    res = run(m, "pledge", 0, heading=0.0)
    assert res.outcome is Outcome.SOLVED and len(res.path) == 6


def test_agents_use_only_probe():
    import inspect
    import mazerunner.solvers.chain as ch
    import mazerunner.solvers.pledge as pl
    import mazerunner.solvers.random_mouse as rm
    import mazerunner.solvers.tremaux as tx
    import mazerunner.solvers.wall_follower as wf
    for mod in (ch, pl, rm, tx, wf):
        assert "_maze" not in inspect.getsource(mod)


def test_registrations_implemented():
    for k in ALL_KEYS:
        assert solvers.get(k).implemented, k


# --------------------------------------------------------- all topologies
@pytest.mark.parametrize("name,size", [("square", (6, 7)), ("polar", (4,)), ("hex", (5, 6))])
def test_all_compatible_solvers_on_topologies(name, size):
    try:
        topo = make_topology(name, size)
        topo.cell_list
        topo.neighbors(topo.cell_list[0])
    except NotImplementedError:
        pytest.skip(f"{name} not implemented")
    for seed in range(3):
        try:
            m = carve(topo, seed, braid=0.1 if seed else 0.0)
        except NotImplementedError:
            pytest.skip(f"{name} not implemented")
        for info in solvers.all():
            if not info.implemented or not info.compatible(topo.traits)[0]:
                continue
            res = solve(m, info.key, seed, params={"step_budget": 200_000})
            if info.key in OPTIMAL + NONOPT_OMNI:
                assert res.outcome is Outcome.SOLVED, (name, info.key)
                assert m.verify_path(res.path), (name, info.key)
                if info.key in OPTIMAL:
                    assert len(res.path) == m.shortest_path_length() + 1, (name, info.key)
            elif info.key in ("tremaux", "random-mouse"):
                assert res.outcome is Outcome.SOLVED, (name, info.key)
                check_linked_trail(m, res.path)
            else:
                assert res.outcome in tuple(Outcome)
                check_linked_trail(m, res.path)
