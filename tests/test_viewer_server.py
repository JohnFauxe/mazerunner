import json
import random
import shutil
import subprocess
import threading
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

import pytest

from mazerunner import api
from mazerunner.core.traits import Trait
from mazerunner.core.registry import Phase, generators, solvers
from mazerunner.generators.base import Generator
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult
from mazerunner.viewer import server as vs

if "_v-dfs" not in generators:
    @generators.register("_v-dfs", title="test dfs", phase=Phase.MVP, implemented=True)
    class _Dfs(Generator):
        def carve(self, maze, rng):
            cells = list(maze.topology.cells())
            start = rng.choice(cells)
            seen, stack = {start}, [start]
            while stack:
                c = stack[-1]
                self.tracer.emit("current", c)
                nb = [n for n in maze.topology.neighbors(c) if n not in seen]
                if not nb:
                    stack.pop()
                    continue
                n = rng.choice(nb)
                maze.link(c, n)
                seen.add(n)
                stack.append(n)

if "_v-needs" not in generators:
    @generators.register("_v-needs", title="x", requires=[Trait.WEAVE], phase=Phase.MVP,
                         implemented=True)
    class _Needs(_Dfs):
        pass

if "_v-bfs" not in solvers:
    @solvers.register("_v-bfs", title="test bfs", phase=Phase.MVP, implemented=True)
    class _Bfs(OmniscientSolver):
        def solve(self, maze, rng):
            prev, q = {maze.start: None}, deque([maze.start])
            n = 0
            while q:
                c = q.popleft()
                n += 1
                self.tracer.emit("visit", c)
                if c == maze.goal:
                    break
                for nb in maze.passages(c):
                    if nb not in prev:
                        prev[nb] = c
                        self.tracer.emit("frontier_add", nb)
                        q.append(nb)
            path, c = [], maze.goal
            while c is not None:
                path.append(c)
                c = prev[c]
            return SolveResult(Outcome.SOLVED, path[::-1], {"nodes_expanded": n})


@pytest.fixture
def srv(tmp_path):
    (tmp_path / "traces").mkdir()
    (tmp_path / "results").mkdir()
    s = vs.make_server(port=0, traces_dir=tmp_path / "traces", results_dir=tmp_path / "results")
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    s.base = f"http://127.0.0.1:{s.server_address[1]}"
    s.tmp = tmp_path
    yield s
    s.shutdown()
    s.server_close()


def get(srv, path):
    return urllib.request.urlopen(srv.base + path, timeout=10)


def get_json(srv, path):
    with get(srv, path) as r:
        return json.load(r)


def post(srv, path, body):
    req = urllib.request.Request(srv.base + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=20)


CFG = {"topology": "square", "size": [6, 6], "generator": "_v-dfs", "solvers": ["_v-bfs"],
       "seed": 3, "endpoints": {"placement": "opposite-sides"}}


def test_index_and_static(srv):
    with get(srv, "/") as r:
        assert "text/html" in r.headers["Content-Type"]
        assert b"<html" in r.read()
    with get(srv, "/app.js") as r:
        assert "javascript" in r.headers["Content-Type"]


@pytest.mark.parametrize("p", ["/../server.py", "/%2e%2e/server.py", "/..%2fserver.py",
                               "/static/../../server.py", "/nope.js"])
def test_path_traversal(srv, p):
    with pytest.raises(urllib.error.HTTPError) as e:
        get(srv, p)
    assert e.value.code in (403, 404)


def test_catalog(srv):
    c = get_json(srv, "/api/catalog")
    sq = next(t for t in c["topologies"] if t["key"] == "square")
    assert sq["default_size"] == [20, 20] and "ORTHOGONAL" in sq["traits"]
    assert any(g["key"] == "_v-dfs" for g in c["generators"])
    assert {"key", "title", "requires", "implemented", "tags"} <= set(c["solvers"][0])
    assert "opposite-sides" in c["placements"]


def test_run(srv):
    with post(srv, "/api/run", {**CFG, "solvers": ["_v-bfs"]}) as r:
        d = json.load(r)
    assert d["header"]["geometry"]["cells"]
    assert d["generation"]
    s = d["solves"]["_v-bfs"]
    assert s["events"] and s["result"]["outcome"] == "solved"
    assert s["result"]["path_len"] - 1 == s["result"]["optimal"]  # cells vs edges


def test_run_errors(srv):
    with pytest.raises(urllib.error.HTTPError) as e:
        post(srv, "/api/run", {**CFG, "generator": "nope"})
    assert e.value.code == 400 and "error" in json.load(e.value)
    with pytest.raises(urllib.error.HTTPError) as e:
        post(srv, "/api/run", {**CFG, "size": [1000, 1000]})
    assert e.value.code == 400
    # incompatible traits
    with pytest.raises(urllib.error.HTTPError) as e:
        post(srv, "/api/run", {**CFG, "generator": "_v-needs"})
    assert e.value.code == 400


def test_live(srv):
    url = ("/api/live?topology=square&size=5,5&generator=_v-dfs&solvers=_v-bfs"
           "&seed=1&placement=opposite-sides&delay=0")
    events = []
    with get(srv, url) as r:
        assert "text/event-stream" in r.headers["Content-Type"]
        cur = None
        for raw in r:
            line = raw.decode().rstrip("\n")
            if line.startswith("event: "):
                cur = line[7:]
            elif line.startswith("data: "):
                events.append((cur, json.loads(line[6:])))
    names = [n for n, _ in events]
    assert names[0] == "header" and names[-1] == "done"
    order = [n for n in dict.fromkeys(names)]
    assert [o for o in order if o != "maze"] == ["header", "gen", "solve-start", "solve",
                                                 "solve-end", "done"]
    assert events[0][1]["geometry"]["cells"]
    end = next(d for n, d in events if n == "solve-end")
    assert end["result"]["outcome"] == "solved"


def test_traces(srv):
    out = srv.tmp / "traces" / "t.trace.jsonl"
    api.record("square", (5, 5), "_v-dfs", "_v-bfs", seed=2, out=out)
    lst = get_json(srv, "/api/traces")
    assert lst[0]["name"] == "t.trace.jsonl" and lst[0]["generator"] == "_v-dfs"
    assert lst[0]["seed"] == 2 and lst[0]["topology"] == "square"
    d = get_json(srv, "/api/traces/t.trace.jsonl")
    assert d["header"]["geometry"] and d["events"] and d["footer"]["result"]
    for bad in ("..%2f..%2fetc%2fpasswd", "x.txt", "missing.trace.jsonl"):
        with pytest.raises(urllib.error.HTTPError) as e:
            get(srv, "/api/traces/" + bad)
        assert e.value.code in (400, 404)


def test_results(srv):
    f = srv.tmp / "results" / "r.jsonl"
    rows = [{"kind": "run", "id": 1}, {"kind": "trial", "generator": "g", "solver": "s"}]
    f.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    assert [r["name"] for r in get_json(srv, "/api/results")] == ["r.jsonl"]
    assert get_json(srv, "/api/results/r.jsonl")["rows"] == rows


@pytest.mark.skipif(shutil.which("node") is None, reason="node not available")
def test_js_syntax():
    files = sorted(vs.STATIC.rglob("*.js"))
    assert files
    for f in files:
        r = subprocess.run(["node", "--input-type=module", "--check"], input=f.read_text(),
                           capture_output=True, text=True)
        assert r.returncode == 0, f"{f}: {r.stderr}"


def test_gz_trace_without_geometry_is_served_with_geometry(srv):
    from mazerunner import api
    out = srv.tmp / "traces" / "g.trace.jsonl.gz"
    api.record("square", (4, 4), "_v-dfs", "_v-bfs", 3, out)
    names = [t["name"] for t in get_json(srv, "/api/traces")]
    assert "g.trace.jsonl.gz" in names
    d = get_json(srv, "/api/traces/g.trace.jsonl.gz")
    assert len(d["header"]["geometry"]["cells"]) == 16 and d["events"]
