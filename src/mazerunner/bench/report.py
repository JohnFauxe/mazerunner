"""Summarise results: summary.json, summary.md tables and (if matplotlib is
installed, `report` extra) a few PNG charts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from mazerunner.bench import results


def _fmt(v, kind="f3"):
    if v is None:
        return "-"
    if kind == "ms":
        return f"{v / 1e6:.3f}"
    if kind == "kb":
        return f"{v / 1024:.1f}"
    if kind == "f1":
        return f"{v:.1f}"
    if kind == "pct":
        return f"{100 * v:.0f}%"
    return f"{v:.3f}"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def _size(s) -> str:
    return "x".join(map(str, s))


def _markdown(summary: list[dict]) -> str:
    gens = [s for s in summary if s["section"] == "generation"]
    sols = [s for s in summary if s["section"] == "solve"]
    topos = sorted({s["topology"] for s in summary})
    lines = ["# MazeRunner benchmark summary", ""]
    for topo in topos:
        lines += [f"## {topo}", "", "### Generators: texture and cost", ""]
        rows = []
        for g in (x for x in gens if x["topology"] == topo):
            t = g["texture"]
            rows.append([_size(g["size"]), g["generator"], str(g["n"]),
                         _fmt(g["time_ns_median"], "ms"), _fmt(g["peak_bytes_median"], "kb"),
                         _fmt(t.get("dead_end_ratio")), _fmt(t.get("mean_corridor_length"), "f1"),
                         _fmt(t.get("diameter"), "f1"), _fmt(t.get("perfect"), "pct")])
        lines += [_table(["size", "generator", "n", "time ms", "peak KiB", "dead-end ratio",
                          "mean corridor", "diameter", "perfect"], rows), "",
                  "### Solvers: cost and quality", ""]
        rows = []
        for s in (x for x in sols if x["topology"] == topo):
            rows.append([_size(s["size"]), s["generator"], s["solver"], str(s["n"]),
                         _fmt(s["success_rate"], "pct"), _fmt(s["time_ns_median"], "ms"),
                         _fmt(s["peak_bytes_median"], "kb"), _fmt(s["optimality_mean"]),
                         _fmt(s["nodes_expanded_mean"], "f1"), _fmt(s["steps_mean"], "f1")])
        lines += [_table(["size", "generator", "solver", "n", "success", "time ms", "peak KiB",
                          "optimality", "nodes expanded", "steps"], rows), ""]
    if not topos:
        lines.append("No completed trials.")
    return "\n".join(lines) + "\n"


def _charts(summary: list[dict], out_dir: Path) -> list[Path]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:  # noqa: BLE001 - optional extra
        return []
    files: list[Path] = []
    gens = [s for s in summary if s["section"] == "generation"]
    sols = [s for s in summary if s["section"] == "solve"]
    for topo in sorted({s["topology"] for s in gens}):
        series = defaultdict(list)
        for g in (x for x in gens if x["topology"] == topo):
            cells = g["texture"].get("n_cells")
            if cells and g["time_ns_median"]:
                series[g["generator"]].append((cells, g["time_ns_median"] / 1e6))
        if series:
            fig, ax = plt.subplots(figsize=(6, 4))
            for name, pts in sorted(series.items()):
                pts.sort()
                ax.plot(*zip(*pts), marker="o", label=name)
            ax.set(xscale="log", yscale="log", xlabel="cells", ylabel="median generation time (ms)",
                   title=f"Generation time: {topo}")
            ax.legend(fontsize=6)
            p = out_dir / f"gen_time_{topo}.png"
            fig.savefig(p, dpi=120, bbox_inches="tight")
            plt.close(fig)
            files.append(p)
        de = [(g["generator"], g["texture"]["dead_end_ratio"]) for g in gens
              if g["topology"] == topo and "dead_end_ratio" in g["texture"]
              and g["size"] == max((x["size"] for x in gens if x["topology"] == topo), key=lambda s: s)]
        if de:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar([d[0] for d in de], [d[1] for d in de])
            ax.set(ylabel="dead-end ratio", title=f"Dead ends: {topo} (largest size)")
            ax.tick_params(axis="x", rotation=70, labelsize=7)
            p = out_dir / f"dead_ends_{topo}.png"
            fig.savefig(p, dpi=120, bbox_inches="tight")
            plt.close(fig)
            files.append(p)
        ss = [s for s in sols if s["topology"] == topo]
        if ss:
            big = max(s["size"] for s in ss)
            by = defaultdict(list)
            for s in ss:
                if s["size"] == big:
                    v = s["nodes_expanded_mean"] if s["nodes_expanded_mean"] is not None else s["steps_mean"]
                    if v is not None:
                        by[s["solver"]].append(v)
            if by:
                fig, ax = plt.subplots(figsize=(6, 4))
                names = sorted(by)
                ax.bar(names, [sum(by[n]) / len(by[n]) for n in names])
                ax.set(yscale="log", ylabel="nodes expanded (or steps)",
                       title=f"Solver work: {topo} {_size(big)}")
                ax.tick_params(axis="x", rotation=70, labelsize=7)
                p = out_dir / f"solver_work_{topo}.png"
                fig.savefig(p, dpi=120, bbox_inches="tight")
                plt.close(fig)
                files.append(p)
    return files


def build_report(results_path, out_dir) -> list[Path]:
    """Write summary.json, summary.md and (if matplotlib is available) PNG charts
    into `out_dir`. Returns the files written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = results.summarise(results.load_trials(Path(results_path)))
    js = out_dir / "summary.json"
    js.write_text(json.dumps(summary, indent=2, default=str))
    md = out_dir / "summary.md"
    md.write_text(_markdown(summary))
    return [js, md, *_charts(summary, out_dir)]
