import math
from collections import Counter, deque

import pytest

from mazerunner.topologies.hex import HexGrid
from mazerunner.topologies.polar import PolarGrid

CASES = [("polar", PolarGrid, (n,)) for n in (1, 2, 3, 5, 10)] + \
        [("hex", HexGrid, a) for a in ((1, 1), (1, 5), (4, 4), (7, 9))]
IDS = [f"{n}{a}" for n, _, a in CASES]
EPS = 1e-9


@pytest.fixture(params=CASES, ids=IDS)
def topo(request):
    _, cls, args = request.param
    return cls(*args)


def _on_edge(g, c):
    if g.name == "polar":
        return c[0] == g.rings - 1
    return len(g.neighbors(c)) < 6


def test_graph_basics(topo):
    cs = list(topo.cells())
    assert len(cs) == len(topo) == len(set(cs))
    for a in cs:
        ns = list(topo.neighbors(a))
        assert a not in ns and len(ns) == len(set(ns))
        for b in ns:
            assert b in set(cs) and a in topo.neighbors(b)
    assert topo.describe()["args"]


def test_rows_hooks(topo):
    rows = topo.rows()
    assert sorted(c for r in rows for c in r) == sorted(topo.cells())
    for i, row in enumerate(rows):
        assert row and row[-1] is not None
        assert topo.next_in_row(row[-1]) is None
        for c in row:
            assert topo.row_of(c) == i
            nx = topo.next_in_row(c)
            if nx is not None:
                assert topo.row_of(nx) == i
                assert row.index(nx) == row.index(c) + 1
            for p in topo.prev_row_neighbors(c):
                assert p in topo.neighbors(c) and topo.row_of(p) == i - 1
                assert c in topo.next_row_neighbors(p)
            for q in topo.next_row_neighbors(c):
                assert q in topo.neighbors(c) and topo.row_of(q) == i + 1
                assert c in topo.prev_row_neighbors(q)
    # every cross-row adjacency is covered by the hooks
    for c in topo.cells():
        cross = {n for n in topo.neighbors(c) if topo.row_of(n) != topo.row_of(c)}
        assert cross == set(topo.prev_row_neighbors(c)) | set(topo.next_row_neighbors(c))


def test_boundary(topo):
    b = topo.boundary()
    assert b and all(_on_edge(topo, c) for c in b)
    if len(topo) > 1:
        n = len(b)
        assert b[0] != b[n // 2]
        if topo.name == "polar":
            assert topo.position(b[0])[0] < topo.position(topo.center())[0]  # west
            assert abs(topo.heading(topo.center(), b[0]) - math.pi) < 0.2 or topo.rings < 2


def test_geometry(topo):
    geo = topo.geometry()
    assert len(geo["cells"]) == len(topo)
    inner = [frozenset((w["a"], w["b"])) for w in geo["walls"] if w["b"] is not None]
    expect = {frozenset((topo.index[a], topo.index[b])) for a in topo.cells() for b in topo.neighbors(a)}
    assert set(inner) == expect and max(Counter(inner).values(), default=1) == 1
    assert any(w["b"] is None for w in geo["walls"])
    W, H = geo["width"], geo["height"]
    pts = [p for poly in geo["cells"] for p in poly] + [p for w in geo["walls"] for p in w["pts"]]
    assert all(-EPS <= x <= W + EPS and -EPS <= y <= H + EPS for x, y in pts)
    for c in topo.cells():
        x, y = topo.position(c)
        assert 0 <= x <= W and 0 <= y <= H


def test_heading_range(topo):
    for a in topo.cells():
        for b in topo.neighbors(a):
            assert -math.pi < topo.heading(a, b) <= math.pi


def test_distance_admissible(topo):
    for s in topo.cells():
        dist = {s: 0}
        q = deque([s])
        while q:
            u = q.popleft()
            for v in topo.neighbors(u):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)
        assert len(dist) == len(topo)
        for t, d in dist.items():
            assert topo.distance(s, t) <= d
        assert topo.distance(s, s) == 0


def test_neighbors_ccw_order(topo):
    for a in topo.cells():
        angs = [topo.heading(a, b) % (2 * math.pi) for b in topo.neighbors(a)]
        if len(angs) < 3:
            continue
        # cyclically increasing: at most one wrap-around descent
        descents = sum(1 for i in range(len(angs)) if angs[i] < angs[i - 1])
        assert descents <= 1, (a, angs)
        assert len(set(round(x, 9) for x in angs)) == len(angs)


def test_polar_structure():
    g = PolarGrid(4)
    assert len(g.rows()[0]) == 1 and len(g.rows()[1]) == 6
    assert sorted(g.neighbors((0, 0))) == [(1, i) for i in range(6)]
    for c in g.cells():
        for ch in g.next_row_neighbors(c):
            assert g.prev_row_neighbors(ch) == [c]


def test_hex_structure():
    g = HexGrid(4, 4)
    assert len(g.neighbors((1, 1))) == 6 and len(g.neighbors((0, 0))) == 2
    assert g.distance((0, 0), (3, 3)) == 5


def test_smoke_svg(topo, tmp_path):
    geo = topo.geometry()
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {geo["width"]} {geo["height"]}">']
    for w in geo["walls"]:
        d = " ".join(f"{x:.3f},{y:.3f}" for x, y in w["pts"])
        out.append(f'<polyline points="{d}" fill="none" stroke="black" stroke-width="0.05"/>')
    out.append("</svg>")
    p = tmp_path / "grid.svg"
    p.write_text("\n".join(out))
    assert p.stat().st_size > 100 and out[1].startswith("<polyline")
