import io
import random
import xml.etree.ElementTree as ET

import pytest

from mazerunner.core.maze import Maze
from mazerunner.core.topology import Topology
from mazerunner.core.trace import Recorder, read_trace
from mazerunner.io import serialize
from mazerunner.render import animate, ascii as ascii_r, svg
from mazerunner.topologies.square import SquareGrid
from mazerunner.viewer import terminal


def dfs_maze(rows, cols, seed=1, tracer=None):
    topo = SquareGrid(rows, cols)
    m = Maze(topo, start=(0, 0), goal=(rows - 1, cols - 1), meta={"gen": "dfs", "seed": seed})
    if tracer is not None:
        m.tracer = tracer
    rng = random.Random(seed)
    seen, stack = {(0, 0)}, [(0, 0)]
    while stack:
        c = stack[-1]
        opts = [n for n in topo.neighbors(c) if n not in seen]
        if not opts:
            stack.pop()
            continue
        n = rng.choice(opts)
        seen.add(n)
        m.link(c, n)
        stack.append(n)
    return m


def known_2x3():
    m = Maze(SquareGrid(2, 3), start=(0, 0), goal=(1, 2))
    for a, b in [((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (1, 2)), ((0, 0), (1, 0)),
                 ((1, 0), (1, 1))]:
        m.link(a, b)
    return m


def test_ascii_1x1():
    m = Maze(SquareGrid(1, 1), start=(0, 0), goal=(0, 0))
    assert ascii_r.render(m) == "+---+\n| S |\n+---+"


def test_ascii_2x3_exact():
    m = known_2x3()
    # row 0: S-a-b all linked E; (0,2)-(1,2) linked; (0,0)-(1,0) linked; (1,0)-(1,1) linked
    expected = "\n".join([
        "+---+---+---+",
        "| S         |",
        "+   +---+   +",
        "|       | G |",
        "+---+---+---+",
    ])
    assert ascii_r.render(m) == expected


def test_ascii_path_marks_and_unicode():
    m = known_2x3()
    out = ascii_r.render(m, [(1, 0), (1, 1)], marks={(0, 1): "x"})
    assert " x " in out and out.count("·") == 2
    uni = ascii_r.render(m, style="unicode")
    assert uni.splitlines()[0].startswith("┌") and "┼" not in uni
    assert len(uni.splitlines()) == 5


def test_ascii_rejects_other_topologies():
    class Fake(SquareGrid):
        traits = frozenset()
    with pytest.raises(ValueError):
        ascii_r.render(Maze(Fake(2, 2)))


def test_svg_wellformed_and_wall_count():
    m = known_2x3()
    s = svg.render(m, [(0, 0), (1, 0)], title="t & t")
    root = ET.fromstring(s)
    ns = "{http://www.w3.org/2000/svg}"
    wall = next(p for p in root.iter(ns + "path") if p.get("class") == "w")
    # 2x3 grid: 3*2 + ... perimeter 10 + interior wall segments total 7 - 5 links = 2 -> 12 walls
    assert wall.get("d").count("M") == 12
    assert any(p.get("class") == "p" for p in root.iter(ns + "path"))


def test_svg_fake_topology():
    class Two(Topology):
        name = "two"

        def cells(self):
            yield from "ab"

        def neighbors(self, c):
            return ["b" if c == "a" else "a"]

        def __len__(self):
            return 2

        def boundary(self):
            return ["a", "b"]

        def position(self, c):
            return (0.5, 0.5) if c == "a" else (1.5, 0.5)

        def geometry(self):
            return {"width": 2, "height": 1,
                    "cells": [[[0, 0], [1, 0], [1, 1], [0, 1]], [[1, 0], [2, 0], [2, 1], [1, 1]]],
                    "walls": [{"a": 0, "b": 1, "pts": [[1, 0], [1, 1]]},
                              {"a": 0, "b": None, "pts": [[0, 0], [1, 0]]}]}
    t = Two()
    m = Maze(t, start="a", goal="b")
    s1 = svg.render(m, show_cells={"a": "#abcdef"})
    ET.fromstring(s1)
    assert s1.count("M") >= 1 and "#abcdef" in s1
    n_walls = lambda s: next(p for p in ET.fromstring(s).iter("{http://www.w3.org/2000/svg}path")
                            if p.get("class") == "w").get("d").count("M")
    assert n_walls(s1) == 2
    m.link("a", "b")
    assert n_walls(svg.render(m, ["a", "b"])) == 1


def test_save_svg(tmp_path):
    p = tmp_path / "m.svg"
    svg.save_svg(dfs_maze(4, 4), None, p)
    ET.parse(p)


def test_serialize_roundtrip(tmp_path):
    m = dfs_maze(5, 6, seed=3)
    m2 = serialize.loads(serialize.dumps(m))
    assert m2.links == m.links
    assert (m2.start, m2.goal, m2.meta) == (m.start, m.goal, m.meta)
    assert m2.topology.describe() == m.topology.describe()
    serialize.save(m, tmp_path / "m.json")
    assert serialize.load(tmp_path / "m.json").links == m.links


def make_trace(tmp_path, rows=4, cols=5):
    topo = SquareGrid(rows, cols)
    rec = Recorder(topo.index, {"topology": topo.describe(), "generator": "dfs"})
    m = dfs_maze(rows, cols, seed=2, tracer=rec)
    rec.emit("phase", label="solve:bfs")
    rec.emit("endpoints", m.start, m.goal)
    rec.emit("visit", (0, 0))
    rec.emit("frontier_add", (0, 1))
    rec.emit("current", (0, 1))
    rec.emit("mark", (0, 0), (0, 1), count=2)
    rec.emit("fill", (1, 1))
    rec.emit("mystery", (1, 1))
    rec.emit("path", (0, 0), (0, 1))
    p = tmp_path / "t.trace.jsonl"
    with open(p, "w") as fp:
        rec.dump(fp)
    return p, m, topo


def test_replay_final_links(tmp_path):
    p, m, topo = make_trace(tmp_path)
    with open(p) as fp:
        header, events, _ = read_trace(fp)
    states = list(animate.replay_states(header, events))
    st = states[-1][1]
    idx = topo.index
    assert st["links"] == {tuple(sorted((idx[a], idx[b]))) for a, b in (tuple(e) for e in m.links)}
    assert st["path"] == [0, 1] and st["endpoints"] == (0, idx[m.goal])
    assert st["marks"] == {0: 2} and st["filled"] == {6}
    assert st["visited"] == {0} and st["phase"] == "solve:bfs"


def test_solve_phase_clears(tmp_path):
    ev = [[0, "visit", [1]], [1, "frontier_add", [2]], [2, "current", [2]],
          [3, "phase", [], {"label": "solve: bfs"}]]
    st = list(animate.replay_states({}, ev))[-1][1]
    assert not st["visited"] and not st["frontier"] and st["current"] is None


def test_frame_text_and_play(tmp_path):
    p, m, topo = make_trace(tmp_path)
    with open(p) as fp:
        header, events, _ = read_trace(fp)
    *_, (step, st) = animate.replay_states(header, events)
    txt = terminal.frame_text(st, 4, 5, step=step, total=len(events), color=False)
    assert "phase: solve:bfs" in txt.splitlines()[-1] and "step" in txt
    assert len(txt.splitlines()) == 4 * 2 + 1 + 1
    colored = terminal.frame_text(st, 4, 5, color=True)
    assert "\x1b[" in colored
    buf = io.StringIO()
    terminal.play(p, fps=0, every=7, out=buf)
    assert "phase:" in buf.getvalue()


def test_play_non_square(tmp_path):
    p = tmp_path / "h.jsonl"
    p.write_text('{"type":"header","version":1,"topology":{"name":"hex","args":[3]}}\n')
    buf = io.StringIO()
    terminal.play(p, out=buf)
    assert "mazerunner serve" in buf.getvalue()


def test_animated_svg(tmp_path):
    p, m, topo = make_trace(tmp_path)
    out = tmp_path / "a.svg"
    n = animate.write_animated_svg(p, out, fps=10, every=3, max_frames=12)
    root = ET.parse(out).getroot()
    assert n <= 12 and len(root.findall("{http://www.w3.org/2000/svg}g")) == n
    with open(p) as fp:
        header, events, _ = read_trace(fp)
    frames = animate.to_svg_frames(header, events, every=10)
    assert frames and all(ET.fromstring(f) is not None for f in frames)


def test_open_all_replays_recursive_division():
    import mazerunner.api as api
    from mazerunner.core.trace import Recorder
    from mazerunner.render.animate import replay_states

    topo = api.make_topology("square", (6, 6))
    rec = Recorder(topo.index, api.trace_header(topo))
    maze = api.generate(topo, "recursive-division", 3, tracer=rec)
    final = None
    for _, st in replay_states(rec.header, rec.events):
        final = st
    want = {tuple(sorted((topo.index[a], topo.index[b]))) for a, b in (tuple(e) for e in maze.links)}
    assert final["links"] == want
