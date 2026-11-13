"""Append-only JSON Lines result store (resumable by trial seed) and aggregation."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path


def append(path: Path, row: dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(row, default=str) + "\n")


def load(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_trials(path: Path) -> list[dict]:
    return [r for r in load(path) if r.get("kind") == "trial"]


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _texture_means(textures: list[dict]) -> dict:
    keys: dict[str, None] = {}
    for t in textures:
        for k, v in t.items():
            if isinstance(v, (int, float)):  # bool counts: share of True
                keys[k] = None
    return {k: _mean([float(t[k]) for t in textures
                      if isinstance(t.get(k), (int, float))]) for k in keys}


def summarise(rows: list[dict]) -> list[dict]:
    """Aggregate trial rows (errors excluded).

    Generation aggregates, one per (topology, size, generator), have
    "section": "generation": n (distinct mazes), time_ns_median, peak_bytes_median,
    "texture" (mean of each numeric texture metric), counters_mean.
    Solve aggregates, one per (topology, size, generator, solver), have
    "section": "solve": n, success_rate, time_ns_median, peak_bytes_median,
    optimality_mean, nodes_expanded_mean, steps_mean.
    """
    trials = [r for r in rows if r.get("kind", "trial") == "trial"
              and not r.get("error") and r.get("gen") and r.get("solve")]
    gen_groups: dict[tuple, dict[int, dict]] = defaultdict(dict)
    solve_groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in trials:
        gk = (r["topology"], tuple(r["size"]), r["generator"])
        gen_groups[gk].setdefault(r["seed"], r["gen"])  # one gen record per maze
        solve_groups[gk + (r["solver"],)].append(r["solve"])
    out = []
    for (topo, size, gen), by_seed in sorted(gen_groups.items()):
        gens = list(by_seed.values())
        counters: dict[str, list] = defaultdict(list)
        for g in gens:
            for k, v in g.get("counters", {}).items():
                counters[k].append(v)
        out.append({
            "section": "generation", "topology": topo, "size": list(size), "generator": gen,
            "n": len(gens),
            "time_ns_median": _median([g["time_ns_median"] for g in gens]),
            "peak_bytes_median": _median([g["peak_bytes"] for g in gens]),
            "texture": _texture_means([g.get("texture") or {} for g in gens]),
            "counters_mean": {k: _mean(v) for k, v in counters.items()},
        })
    for (topo, size, gen, sol), ss in sorted(solve_groups.items()):
        out.append({
            "section": "solve", "topology": topo, "size": list(size), "generator": gen,
            "solver": sol, "n": len(ss),
            "success_rate": sum(s["outcome"] == "solved" for s in ss) / len(ss),
            "time_ns_median": _median([s["time_ns_median"] for s in ss]),
            "peak_bytes_median": _median([s["peak_bytes"] for s in ss]),
            "optimality_mean": _mean([s.get("optimality") for s in ss]),
            "nodes_expanded_mean": _mean([s.get("counters", {}).get("nodes_expanded") for s in ss]),
            "steps_mean": _mean([s.get("steps") for s in ss]),
        })
    return out
