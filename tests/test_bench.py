import json
import random
from collections import deque

import pytest

from mazerunner.bench import results
from mazerunner.bench.matrix import RunSettings, expand, load_config
from mazerunner.bench.report import build_report
from mazerunner.bench.runner import run_config
from mazerunner.core.registry import Phase, generators, load_all, solvers, topologies
from mazerunner.solvers.base import OmniscientSolver, Outcome, SolveResult
from mazerunner.topologies.square import SquareGrid

from test_metrics import _TestDFS  # noqa: F401  registers "_t-dfs" (guarded)

load_all()

if "_t-bfs" not in solvers:
    @solvers.register("_t-bfs", title="test bfs", phase=Phase.MVP, implemented=True)
    class _TestBFS(OmniscientSolver):
        def solve(self, maze, rng):
            prev, q = {maze.start: None}, deque([maze.start])
            while q:
                c = q.popleft()
                if c == maze.goal:
                    break
                for n in maze.passages(c):
                    if n not in prev:
                        prev[n] = c
                        q.append(n)
            path, c = [], maze.goal
            while c is not None:
                path.append(c)
                c = prev[c]
            return SolveResult(Outcome.SOLVED, path[::-1], {"nodes_expanded": len(prev)})

if "_t-unimpl" not in generators:
    @generators.register("_t-unimpl", title="x", phase=Phase.MVP, implemented=False)
    class _Unimpl(_TestDFS):
        pass

if "_t-notopo" not in topologies:
    @topologies.register("_t-notopo", title="x", phase=Phase.MVP)
    class _NoTopo(SquareGrid):
        name = "_t-notopo"

        def __init__(self, *a):
            raise NotImplementedError


def _cfg(**over):
    cfg = {"seed": 5, "trials": 2, "warmup": 0, "repeats": 2,
           "generators": ["_t-dfs"], "solvers": ["_t-bfs"],
           "topology": [{"name": "square", "sizes": [[4, 4], [6, 5]]}],
           "endpoints": {"placement": "opposite-sides"},
           "trace": {"record": True, "sample": 1, "dir": "traces"}}
    cfg.update(over)
    return cfg


def test_expand_skips():
    cfg = _cfg(generators=["_t-dfs", "_t-unimpl", "binary-tree"],
               topology=[{"name": "square", "sizes": [[3, 3]]},
                         {"name": "_t-notopo", "sizes": [[3, 3]]},
                         {"name": "hex", "sizes": [[3, 3]]}])
    trials, skips = expand(cfg)
    s = {(x.topology, x.algorithm): x.reason for x in skips}
    assert s[("square", "_t-unimpl")] == "not implemented"
    assert s[("_t-notopo", "*")] == "not implemented"
    assert ("hex", "binary-tree") in s
    assert not any(t.generator == "_t-unimpl" for t in trials)
    assert not any(t.topology == "_t-notopo" for t in trials)
    assert all(t.topology == "square" or t.generator != "binary-tree" for t in trials)


def test_expand_seed_excludes_solver():
    trials, _ = expand(_cfg(solvers=["_t-bfs", "_t-bfs"]))
    assert len(trials) == 8 and len({t.maze_key for t in trials}) == 4


def test_run_settings():
    s = RunSettings.from_config(_cfg(warmup=2, repeats=3))
    assert (s.warmup, s.repeats, s.trace_record, s.trace_sample, s.placement) == \
        (2, 3, True, 1, "opposite-sides")


TRIAL_KEYS = {"kind", "topology", "size", "generator", "solver", "braid", "trial", "seed",
              "endpoints", "gen", "solve", "trace", "error"}


def _write_toml(path, cfg):
    def val(v):
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return repr(v)
        if isinstance(v, str):
            return json.dumps(v)
        return "[" + ", ".join(val(x) for x in v) + "]"
    lines = [f"{k} = {val(v)}" for k, v in cfg.items() if not isinstance(v, (dict, list)) or k in
             ("generators", "solvers")]
    for t in cfg["topology"]:
        lines += ["[[topology]]"] + [f"{k} = {val(v)}" for k, v in t.items()]
    for sec in ("endpoints", "trace"):
        lines += [f"[{sec}]"] + [f"{k} = {val(v)}" for k, v in cfg[sec].items()]
    path.write_text("\n".join(lines) + "\n")


def test_run_end_to_end_resume_report(tmp_path):
    cfg_path = tmp_path / "c.toml"
    _write_toml(cfg_path, _cfg())
    out = tmp_path / "res" / "out.jsonl"
    written = run_config(cfg_path, out, progress=False)
    rows = results.load(out)
    assert rows[0]["kind"] == "run" and {"config", "started", "python", "platform"} <= set(rows[0])
    trials = results.load_trials(out)
    assert len(trials) == 4  # 2 sizes x 2 trials
    for r in trials:
        assert set(r) == TRIAL_KEYS and r["error"] is None, r["error"]
        assert set(r["gen"]) == {"time_ns_median", "time_ns", "peak_bytes", "counters", "texture"}
        assert len(r["gen"]["time_ns"]) == 2 and r["gen"]["peak_bytes"] > 0
        assert set(r["solve"]) == {"time_ns_median", "time_ns", "peak_bytes", "outcome", "path_len",
                                   "steps", "optimal_len", "optimality", "counters"}
        assert r["solve"]["outcome"] == "solved" and r["solve"]["optimality"] == 1.0
        assert r["gen"]["texture"]["perfect"] is True
        assert r["endpoints"] == "opposite-sides"
    traced = [r for r in trials if r["trace"]]
    assert len(traced) == 2 and all(r["trial"] == 0 for r in traced)
    for r in traced:
        p = out.parent / r["trace"]
        assert r["trace"].startswith("traces/") and p.exists()
        assert r["trace"].endswith(".trace.jsonl.gz")
        from mazerunner.core.trace import load_trace, read_trace_header
        first = read_trace_header(p)
        assert first["type"] == "header" and first["geometry"] is None  # stored without geometry
        header, events, _ = load_trace(p)
        assert header["geometry"]["cells"] and events  # rebuilt on load
    # resumable
    run_config(cfg_path, out, progress=False)
    assert len(results.load_trials(out)) == 4
    assert sum(r["kind"] == "run" for r in results.load(out)) == 2
    # report
    files = build_report(out, tmp_path / "report")
    names = {f.name for f in files}
    assert {"summary.json", "summary.md"} <= names
    summ = json.loads((tmp_path / "report" / "summary.json").read_text())
    assert {s["section"] for s in summ} == {"generation", "solve"}
    md = (tmp_path / "report" / "summary.md").read_text()
    assert "_t-dfs" in md and "_t-bfs" in md


def test_error_is_recorded_not_raised(tmp_path):
    cfg = _cfg(solvers=["_t-bfs"], generators=["_t-dfs"])
    cfg["trace"] = {"record": False}
    cfg["endpoints"] = {"placement": "manual", "start": [0, 0]}  # missing goal -> KeyError
    cfg_path = tmp_path / "c.toml"
    _write_toml(cfg_path, cfg)
    run_config(cfg_path, tmp_path / "o.jsonl", progress=False)
    rows = results.load_trials(tmp_path / "o.jsonl")
    assert rows and all(r["error"] and r["gen"] is None for r in rows)


def test_summarise_aggregates():
    def row(seed, solver, outcome, opt, nodes, t):
        return {"kind": "trial", "topology": "square", "size": [3, 3], "generator": "g",
                "solver": solver, "braid": 0.0, "trial": seed, "seed": seed, "endpoints": "x",
                "gen": {"time_ns_median": t, "time_ns": [t], "peak_bytes": 10, "counters": {},
                        "texture": {"dead_end_ratio": 0.2 * (seed + 1), "perfect": True}},
                "solve": {"time_ns_median": 5, "time_ns": [5], "peak_bytes": 1, "outcome": outcome,
                          "path_len": 3, "steps": 2, "optimal_len": 2, "optimality": opt,
                          "counters": {"nodes_expanded": nodes}},
                "trace": None, "error": None}
    rows = [row(0, "a", "solved", 1.0, 4, 100), row(0, "b", "failed", None, 8, 100),
            row(1, "a", "solved", 0.5, 6, 300), row(1, "b", "solved", 1.0, 10, 300)]
    s = results.summarise(rows)
    g = next(x for x in s if x["section"] == "generation")
    assert g["n"] == 2 and g["time_ns_median"] == 200
    assert g["texture"]["dead_end_ratio"] == pytest.approx(0.3) and g["texture"]["perfect"] == 1.0
    a = next(x for x in s if x["section"] == "solve" and x["solver"] == "a")
    b = next(x for x in s if x["section"] == "solve" and x["solver"] == "b")
    assert a["optimality_mean"] == 0.75 and a["nodes_expanded_mean"] == 5 and a["success_rate"] == 1
    assert b["success_rate"] == 0.5 and b["optimality_mean"] == 1.0


def test_real_registry_smoke(tmp_path):
    cfg = _cfg(generators=["wilson"], solvers=["bfs"], trials=1,
               topology=[{"name": "square", "sizes": [[4, 4]]}])
    cfg["trace"] = {"record": False}
    path = tmp_path / "c.toml"
    _write_toml(path, cfg)
    run_config(path, tmp_path / "o.jsonl", progress=False)
    rows = results.load_trials(tmp_path / "o.jsonl")
    if not rows:
        pytest.skip("wilson/bfs not implemented yet")
    if any(r["error"] and "NotImplementedError" in r["error"] for r in rows):
        pytest.skip("real algorithms not implemented yet")
    assert all(r["error"] is None for r in rows)
