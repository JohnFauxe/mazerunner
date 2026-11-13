"""Execute trials: generate once per maze, time, validate, solve, record (PLAN §4).

Design notes
- Same maze for every solver: trials are grouped by maze key (solver excluded);
  the maze used by the solvers comes from one untimed generation.
- Timing: time.perf_counter_ns, `warmup` untimed + `repeats` timed runs, median
  stored with all samples. Topology construction is not timed. Generation time
  includes braiding and endpoint placement (everything api.generate does).
- Memory: tracemalloc peak on a separate run, never while timing.
- Errors are caught per trial and stored in the row's "error"; a failed part
  has its dict set to None. Wall-clock timeouts are not used (agents have step budgets).
- Resumable: (seed, solver) pairs already in the output file are skipped.
"""

from __future__ import annotations

import platform
import statistics
import sys
import time
import tracemalloc
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from mazerunner import api
from mazerunner.bench import results
from mazerunner.bench.matrix import RunSettings, Skip, Trial, expand, load_config
from mazerunner.core.registry import generators
from mazerunner.metrics.solve import solve_metrics
from mazerunner.metrics.structure import texture


def _time(fn, warmup: int, repeats: int) -> list[int]:
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(max(1, repeats)):
        t0 = time.perf_counter_ns()
        fn()
        samples.append(time.perf_counter_ns() - t0)
    return samples


def _peak(fn) -> int:
    tracemalloc.start()
    try:
        fn()
        return tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()


def trace_name(t: Trial) -> str:
    return (f"{t.topology}-{'x'.join(map(str, t.size))}-{t.generator}-{t.solver}"
            f"-b{t.braid}-t{t.trial}.trace.jsonl.gz")


def _resolve_trace_dir(settings: RunSettings, out_path: Path | None) -> tuple[Path, Path | None]:
    """(directory to write into, directory the row path is relative to)."""
    d = Path(settings.trace_dir)
    if d.is_absolute() or out_path is None:
        return d, None
    return Path(out_path).parent / d, Path(out_path).parent


def _base_row(t: Trial, settings: RunSettings) -> dict:
    return {"kind": "trial", "topology": t.topology, "size": list(t.size),
            "generator": t.generator, "solver": t.solver, "braid": t.braid,
            "trial": t.trial, "seed": t.seed, "endpoints": settings.placement,
            "gen": None, "solve": None, "trace": None, "error": None}


def run_group(group: list[Trial], settings: RunSettings, *, out_path: Path | None = None) -> list[dict]:
    """Run all trials sharing one maze. Returns one row per trial."""
    first = group[0]
    rows = [_base_row(t, settings) for t in group]
    ep = dict(settings.endpoints)

    def fail(msg):
        for r in rows:
            r["error"] = r["error"] or msg

    try:
        topo = api.make_topology(first.topology, first.size)

        def gen():
            return api.generate(topo, first.generator, first.seed, endpoints=dict(ep),
                                braid=first.braid)

        maze = gen()  # untimed: the maze every solver in this group works on
        samples = _time(gen, settings.warmup, settings.repeats)
        peak = _peak(gen)
        gen_rec = {"time_ns_median": int(statistics.median(samples)), "time_ns": samples,
                   "peak_bytes": peak, "counters": dict(maze.meta.get("counters", {})),
                   "texture": texture(maze)}
        for r in rows:
            r["gen"] = gen_rec
        cls = generators.get(first.generator).obj
        if getattr(cls, "produces_perfect", True) and first.braid == 0 and not maze.is_perfect():
            fail(f"generator {first.generator} produced a non-perfect maze")
    except Exception as e:  # noqa: BLE001 - record and carry on
        fail(f"generation: {type(e).__name__}: {e}")
        return rows

    trace_dir, rel_to = _resolve_trace_dir(settings, out_path)
    for t, row in zip(group, rows):
        try:
            def sol(t=t):
                return api.solve(maze, t.solver, t.seed)

            result = sol()
            m = solve_metrics(maze, result)
            samples = _time(sol, settings.warmup, settings.repeats)
            peak = _peak(sol)
            row["solve"] = {
                "time_ns_median": int(statistics.median(samples)), "time_ns": samples,
                "peak_bytes": peak, "outcome": m["outcome"], "path_len": m["path_len"],
                "steps": m["steps"], "optimal_len": m["optimal_len"],
                "optimality": m["optimality"], "counters": m["counters"]}
            if m["outcome"] == "solved" and not m["valid"]:
                row["error"] = row["error"] or "solver returned an invalid path"
        except Exception as e:  # noqa: BLE001
            row["error"] = row["error"] or f"solve: {type(e).__name__}: {e}"
        if settings.trace_record and t.trial < settings.trace_sample:
            try:
                p = api.record(t.topology, t.size, t.generator, t.solver, t.seed,
                               trace_dir / trace_name(t), endpoints=dict(ep), braid=t.braid)
                row["trace"] = (p.relative_to(rel_to) if rel_to else p).as_posix()
            except Exception as e:  # noqa: BLE001
                row["error"] = row["error"] or f"trace: {type(e).__name__}: {e}"
    return rows


def run_trial(trial: Trial, settings: RunSettings | None = None, *, out_path: Path | None = None) -> dict:
    """Run a single trial (its own maze). Prefer `run` so solvers share mazes."""
    return run_group([trial], settings or RunSettings(), out_path=out_path)[0]


def _done_keys(path: Path) -> set[tuple[int, str]]:
    if not path.exists():
        return set()
    return {(r["seed"], r["solver"]) for r in results.load_trials(path)}


def run(trials: list[Trial], out_path, *, settings: RunSettings | None = None,
        config: dict | None = None, skips: list[Skip] | None = None,
        progress: bool = True) -> list[dict]:
    """Run trials, appending rows to the JSONL at `out_path` as groups complete.
    Returns the rows written this invocation (header and skip rows included)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    settings = settings or RunSettings()
    written: list[dict] = []

    def emit(row):
        results.append(out_path, row)
        written.append(row)

    emit({"kind": "run", "config": config or {}, "started": datetime.now(timezone.utc).isoformat(),
          "python": platform.python_version(), "platform": platform.platform()})
    for s in skips or []:
        emit({"kind": "skip", "topology": s.topology, "algorithm": s.algorithm, "reason": s.reason})

    done = _done_keys(out_path)
    groups: dict[tuple, list[Trial]] = defaultdict(list)
    for t in trials:
        if (t.seed, t.solver) not in done:
            groups[t.maze_key].append(t)
    total = sum(len(g) for g in groups.values())
    n = 0
    t0 = time.perf_counter()
    for group in groups.values():
        for row in run_group(group, settings, out_path=out_path):
            emit(row)
        n += len(group)
        if progress:
            f = group[0]
            print(f"[{n}/{total}] {f.topology} {'x'.join(map(str, f.size))} {f.generator} "
                  f"t{f.trial} ({time.perf_counter() - t0:.1f}s)", file=sys.stderr)
    return written


def run_config(config_path, out_path, *, progress: bool = True) -> list[dict]:
    """Load a TOML config, expand it and run it. `out_path` is the results JSONL."""
    cfg = load_config(Path(config_path))
    trials, skips = expand(cfg)
    return run(trials, out_path, settings=RunSettings.from_config(cfg), config=cfg,
               skips=skips, progress=progress)
