"""Generator tests: perfection, determinism, topology-agnosticism, braiding."""
import random

import pytest

from mazerunner.core.registry import generators, load_all, topologies
from mazerunner.core.topology import Topology
from mazerunner.core.trace import Recorder
from mazerunner.generators.braid import braid
from mazerunner.topologies.square import SquareGrid

load_all()

GENS = [g for g in generators.all() if g.implemented]
SIZES = [(1, 1), (1, 5), (5, 1), (2, 2), (10, 10), (30, 17)]
SEEDS = [0, 1, 7]
SQUARE_TRAITS = SquareGrid(2, 2).traits


def make(info, **kw):
    return info.obj(**kw)


def run(info, topo, seed, **kw):
    return make(info, **kw).generate(topo, random.Random(seed))


class GraphTopology(Topology):
    """Random connected planar-ish graph: a path backbone plus random chords. No traits."""
    name = "graph"
    traits = frozenset()

    def __init__(self, n=40, seed=3):
        rnd = random.Random(seed)
        self._n = n
        adj = {i: set() for i in range(n)}
        for i in range(1, n):
            j = rnd.randrange(max(0, i - 4), i)
            adj[i].add(j); adj[j].add(i)
        for _ in range(n):
            a = rnd.randrange(n); b = min(n - 1, a + rnd.randrange(1, 5))
            if a != b:
                adj[a].add(b); adj[b].add(a)
        self._adj = {i: tuple(sorted(s)) for i, s in adj.items()}

    def cells(self):
        return iter(range(self._n))

    def neighbors(self, cell):
        return self._adj[cell]

    def __len__(self):
        return self._n

    def boundary(self):
        return list(range(self._n))

    def position(self, cell):
        return (float(cell), 0.0)

    def geometry(self):
        return {"width": float(self._n), "height": 1.0, "cells": [], "walls": []}


def links_of(maze):
    return frozenset(maze.links)


@pytest.mark.parametrize("info", GENS, ids=lambda i: i.key)
@pytest.mark.parametrize("size", SIZES, ids=lambda s: f"{s[0]}x{s[1]}")
@pytest.mark.parametrize("seed", SEEDS)
def test_square(info, size, seed):
    topo = SquareGrid(*size)
    m = run(info, topo, seed)
    if info.obj.produces_perfect:
        assert m.is_perfect()
    else:
        assert m.n_links <= len(topo) * 2
    assert links_of(m) == links_of(run(info, topo, seed))


@pytest.mark.parametrize("info", GENS, ids=lambda i: i.key)
def test_seeds_differ(info):
    topo = SquareGrid(10, 10)
    assert len({links_of(run(info, topo, s)) for s in range(4)}) > 1


@pytest.mark.parametrize("info", [g for g in GENS if not g.requires], ids=lambda i: i.key)
@pytest.mark.parametrize("seed", SEEDS)
def test_trait_free_on_graph(info, seed):
    topo = GraphTopology()
    m = run(info, topo, seed)
    assert m.is_perfect()
    assert links_of(m) == links_of(run(info, topo, seed))
    for c in topo.cells():
        for n in m.passages(c):
            assert n in topo.neighbors(c)


@pytest.mark.parametrize("strategy", ["newest", "random", "oldest", "middle", "mix"])
def test_growing_tree_strategies(strategy):
    info = generators.get("growing-tree")
    assert run(info, SquareGrid(12, 9), 2, strategy=strategy, mix=0.3).is_perfect()
    assert run(info, GraphTopology(), 2, strategy=strategy).is_perfect()
    with pytest.raises(ValueError):
        make(info, strategy="bogus")


@pytest.mark.parametrize("switch", [0.0, 0.1, 0.5, 1.0])
def test_hybrid_switch(switch):
    info = generators.get("ab-wilson-hybrid")
    assert run(info, SquareGrid(8, 8), 1, switch=switch).is_perfect()


def test_cellular_params():
    info = generators.get("cellular-automaton")
    assert not info.obj.produces_perfect
    for gens, fill in [(0, 0.5), (5, 0.2), (20, 0.9)]:
        m = run(info, SquareGrid(12, 12), 3, generations=gens, fill=fill)
        assert m.n_links >= 0


def test_division_unlinks_walls():
    rec = Recorder(SquareGrid(6, 6).index)
    m = generators.get("recursive-division").obj().generate(
        SquareGrid(6, 6), random.Random(1), tracer=rec)
    assert any(e[1] == "uncarve" for e in rec.events)
    assert m.is_perfect()


@pytest.mark.parametrize("info", [g for g in GENS if g.obj.produces_perfect], ids=lambda i: i.key)
def test_tracing_does_not_change_result(info):
    topo = SquareGrid(7, 6)
    rec = Recorder(topo.index)
    traced = info.obj().generate(topo, random.Random(5), tracer=rec)
    assert links_of(traced) == links_of(run(info, topo, 5))
    assert any(e[1] in ("carve", "uncarve") for e in rec.events)


def _topology_cases():
    args = {"square": (6, 7), "polar": (4,), "hex": (5, 6)}
    for t in topologies.all():
        if t.implemented:
            yield t, args.get(t.key, (5,))


@pytest.mark.parametrize("tinfo,targs", list(_topology_cases()), ids=lambda x: getattr(x, "key", None))
def test_all_topologies(tinfo, targs):
    try:
        topo = tinfo.obj(*targs)
    except NotImplementedError:
        pytest.skip(f"{tinfo.key} not implemented")
    ran = 0
    for g in GENS:
        if not g.obj.produces_perfect:
            continue
        ok, _ = g.compatible(topo.traits)
        if not ok:
            continue
        for seed in (0, 1):
            m = run(g, topo, seed)
            assert m.is_perfect(), f"{g.key} on {tinfo.key}"
        ran += 1
    assert ran > 0


@pytest.mark.parametrize("seed", SEEDS)
def test_braid_full_removes_dead_ends(seed):
    topo = SquareGrid(12, 9)
    m = run(generators.get("recursive-backtracker"), topo, seed)
    assert any(m.degree(c) == 1 for c in topo.cells())
    braid(m, 1.0, random.Random(seed))
    assert not any(m.degree(c) == 1 for c in topo.cells())
    assert m.is_connected()


def test_braid_zero_noop_and_partial():
    topo = SquareGrid(12, 9)
    m = run(generators.get("kruskal"), topo, 1)
    before = links_of(m)
    braid(m, 0.0, random.Random(1))
    assert links_of(m) == before
    ends = sum(m.degree(c) == 1 for c in topo.cells())
    braid(m, 0.5, random.Random(1))
    assert 0 < sum(m.degree(c) == 1 for c in topo.cells()) < ends
    assert before < links_of(m)


def test_braid_deterministic_graph():
    topo = GraphTopology()
    a = run(generators.get("wilson"), topo, 1)
    b = run(generators.get("wilson"), topo, 1)
    braid(a, 0.7, random.Random(2))
    braid(b, 0.7, random.Random(2))
    assert links_of(a) == links_of(b)
