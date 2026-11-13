"""mazerunner CLI.

    mazerunner list
    mazerunner generate -t hex -s 15 15 -g wilson --ascii --svg out.svg --save maze.json
    mazerunner solve maze.json --solver astar --ascii
    mazerunner bench benchmarks/configs/smoke.toml [--dry-run]
    mazerunner report results/results.jsonl
    mazerunner record -t polar -s 10 -g wilson --solver astar
    mazerunner replay traces/x.trace.jsonl [--web | --svg out.svg]
    mazerunner watch -t hex -s 15 15 -g wilson --solvers astar,bfs
    mazerunner serve
    mazerunner uniformity -g wilson -s 3 3
"""

from __future__ import annotations

import argparse
import sys
import urllib.parse
from pathlib import Path

from mazerunner.core.endpoints import Placement
from mazerunner.core.registry import generators, load_all, solvers, topologies


# --- helpers ------------------------------------------------------------------

def _maze_args(p: argparse.ArgumentParser, *, solver: bool = False) -> None:
    p.add_argument("-t", "--topology", default="square")
    p.add_argument("-s", "--size", type=int, nargs="+", default=None,
                   help="square/hex: ROWS COLS, polar: RINGS (default per topology)")
    p.add_argument("-g", "--generator", default="recursive-backtracker")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--placement", default=Placement.OPPOSITE_SIDES.value,
                   choices=[x.value for x in Placement if x is not Placement.MANUAL])
    p.add_argument("--side", type=float, default=0.0,
                   help="which pair of sides, as a boundary fraction (square: 0 W→E, 0.25 S→N)")
    p.add_argument("--along", choices=["center", "random"], default="center")
    p.add_argument("--braid", type=float, default=0.0, help="fraction of dead ends removed")
    if solver:
        p.add_argument("--solver", default="bfs")


_DEFAULT_SIZE = {"square": [20, 20], "hex": [15, 15], "polar": [10]}


def _size(a) -> list[int]:
    return a.size or _DEFAULT_SIZE.get(a.topology, [8, 8])


def _endpoints(a) -> dict:
    ep = {"placement": a.placement}
    if a.placement == "opposite-sides":
        ep.update(side=a.side, along=a.along)
    elif a.placement == "center-out":
        ep.update(side=a.side)
    return ep


def _build(a):
    from mazerunner import api
    topo = api.make_topology(a.topology, _size(a))
    return api.generate(topo, a.generator, a.seed, endpoints=_endpoints(a), braid=a.braid)


def _show(maze, path, a) -> None:
    if getattr(a, "ascii", False):
        from mazerunner.render import ascii as asc
        try:
            print(asc.render(maze, path, style="unicode" if a.unicode else "box"))
        except ValueError as e:
            print(f"(ascii) {e} — use --svg", file=sys.stderr)
    if getattr(a, "svg", None):
        from mazerunner.render.svg import save_svg
        save_svg(maze, path, a.svg)
        print(f"wrote {a.svg}", file=sys.stderr)


def _view_args(p):
    p.add_argument("--ascii", action="store_true", help="print ASCII (square only)")
    p.add_argument("--unicode", action="store_true", help="box-drawing characters for --ascii")
    p.add_argument("--svg", metavar="FILE", help="write an SVG")


# --- commands -------------------------------------------------------------------

def cmd_list(_a) -> None:
    load_all()
    for reg in (topologies, generators, solvers):
        print(f"\n{reg.kind.upper().replace('Y', 'IE')}S")
        for i in reg.all():
            status = "ready" if i.implemented else f"phase {i.phase.value}"
            if reg is topologies:
                req = "has=" + ",".join(sorted(t.name for t in i.obj.traits))
            else:
                req = "needs=" + (",".join(sorted(t.name for t in i.requires)) or "-")
            print(f"  {i.key:22} {status:9} {req:34} {','.join(sorted(i.tags))}")


def cmd_generate(a) -> None:
    from mazerunner.metrics.structure import texture
    maze = _build(a)
    t = texture(maze)
    print(f"{a.generator} on {a.topology} {_size(a)} seed={a.seed}: {len(maze.topology)} cells, "
          f"{maze.n_links} links, perfect={t['perfect']}, dead ends={t['dead_end_ratio']:.1%}, "
          f"diameter={t['diameter']}", file=sys.stderr)
    _show(maze, None, a)
    if a.save:
        from mazerunner.io.serialize import save
        save(maze, a.save)
        print(f"wrote {a.save}", file=sys.stderr)


def cmd_solve(a) -> None:
    from mazerunner import api
    from mazerunner.metrics.solve import solve_metrics
    if a.maze:
        from mazerunner.io.serialize import load
        maze = load(a.maze)
    else:
        maze = _build(a)
    r = api.solve(maze, a.solver, a.seed)
    m = solve_metrics(maze, r)
    print(f"{a.solver}: {m['outcome']} steps={m['steps']} optimal={m['optimal_len']} "
          f"optimality={m['optimality']} counters={r.counters}", file=sys.stderr)
    _show(maze, r.path, a)


def cmd_bench(a) -> None:
    from mazerunner.bench.matrix import expand, load_config
    trials, skips = expand(load_config(Path(a.config)))
    print(f"{len(trials)} trials, {len(skips)} skipped pairings", file=sys.stderr)
    for s in skips:
        print(f"  skip {s.topology:8} {s.algorithm:22} {s.reason}", file=sys.stderr)
    if a.dry_run:
        return
    from mazerunner.bench.runner import run_config
    run_config(Path(a.config), Path(a.out))
    print(f"results → {a.out}   (next: mazerunner report {a.out})", file=sys.stderr)


def cmd_report(a) -> None:
    from mazerunner.bench.report import build_report
    out = Path(a.out) if a.out else Path(a.results).with_suffix("").parent / "report"
    for f in build_report(Path(a.results), out):
        print(f"wrote {f}")


def cmd_record(a) -> None:
    from mazerunner import api
    out = Path(a.out) if a.out else Path("traces") / (
        f"{a.topology}-{'x'.join(map(str, _size(a)))}-{a.generator}-{a.solver or 'gen'}"
        f"-s{a.seed}.trace.jsonl.gz")
    api.record(a.topology, _size(a), a.generator, a.solver, a.seed, out,
               endpoints=_endpoints(a), braid=a.braid)
    print(f"wrote {out}\n  replay: mazerunner replay {out}  (or --web)")


def _serve(a, open_path: str | None) -> None:
    from mazerunner.viewer.server import serve
    url = f"http://{a.host}:{a.port}{open_path or '/'}"
    print(f"MazeRunner viewer on {url}  (Ctrl+C to stop)", file=sys.stderr)
    kw = {"open_path": open_path} if open_path else {}
    try:
        serve(host=a.host, port=a.port, traces_dir=Path(a.traces), results_dir=Path(a.results),
              open_browser=not a.no_open, **kw)
    except KeyboardInterrupt:
        pass


def cmd_replay(a) -> None:
    trace = Path(a.trace)
    if a.svg:
        from mazerunner.render.animate import write_animated_svg
        n = write_animated_svg(trace, Path(a.svg), fps=a.fps, every=a.every)
        print(f"wrote {a.svg} ({n} frames)")
    elif a.web:
        a.traces = str(trace.parent)
        _serve(a, "/?" + urllib.parse.urlencode({"trace": trace.name}))  # .trace.jsonl(.gz)
    else:
        from mazerunner.viewer.terminal import play
        play(trace, fps=a.fps, every=a.every)


def cmd_watch(a) -> None:
    q = {"mode": "race" if a.race else "live", "topology": a.topology,
         "size": ",".join(map(str, _size(a))), "generator": a.generator, "solvers": a.solvers,
         "seed": a.seed, "placement": a.placement, "delay": a.delay, "braid": a.braid}
    _serve(a, "/?" + urllib.parse.urlencode(q))


def cmd_serve(a) -> None:
    _serve(a, None)


def cmd_uniformity(a) -> None:
    from mazerunner import api
    from mazerunner.metrics.uniformity import chi_squared
    topo = api.make_topology(a.topology, a.size)
    r = chi_squared(a.generator, topo, samples=a.samples, seed=a.seed)
    verdict = "consistent with uniform" if r["p_value"] > 0.01 else "NOT uniform"
    print(f"{a.generator} on {a.topology} {a.size}: {r['trees']} spanning trees, {r['samples']} "
          f"samples, chi2={r['chi2']:.1f} (dof {r['dof']}), p={r['p_value']:.4g} → {verdict}")


# --- parser -------------------------------------------------------------------------

def _server_args(p):
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--traces", default="traces")
    p.add_argument("--results", default="results")
    p.add_argument("--no-open", action="store_true", help="don't open a browser")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mazerunner", description="Benchmark maze generation and solving.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="registered topologies and algorithms").set_defaults(func=cmd_list)

    g = sub.add_parser("generate", help="generate one maze")
    _maze_args(g); _view_args(g)
    g.add_argument("--save", metavar="FILE", help="save maze as JSON")
    g.set_defaults(func=cmd_generate)

    s = sub.add_parser("solve", help="solve a saved maze (or generate one)")
    s.add_argument("maze", nargs="?", help="maze JSON from `generate --save`")
    _maze_args(s, solver=True); _view_args(s)
    s.set_defaults(func=cmd_solve)

    b = sub.add_parser("bench", help="run a benchmark matrix")
    b.add_argument("config")
    b.add_argument("--out", default="results/results.jsonl")
    b.add_argument("--dry-run", action="store_true")
    b.set_defaults(func=cmd_bench)

    r = sub.add_parser("report", help="summarise benchmark results")
    r.add_argument("results", nargs="?", default="results/results.jsonl")
    r.add_argument("--out", help="output dir (default: results/report)")
    r.set_defaults(func=cmd_report)

    rec = sub.add_parser("record", help="run once with tracing; save a .trace.jsonl")
    _maze_args(rec)
    rec.add_argument("--solver", default=None, help="omit to record generation only")
    rec.add_argument("--out")
    rec.set_defaults(func=cmd_record)

    rp = sub.add_parser("replay", help="replay a trace (terminal, browser, or animated SVG)")
    rp.add_argument("trace")
    rp.add_argument("--web", action="store_true", help="open in the web viewer")
    rp.add_argument("--svg", metavar="FILE", help="export an animated SVG")
    rp.add_argument("--fps", type=float, default=30.0)
    rp.add_argument("--every", type=int, default=1, help="draw every Nth event")
    _server_args(rp)
    rp.set_defaults(func=cmd_replay)

    w = sub.add_parser("watch", help="run live in the web viewer")
    _maze_args(w)
    w.add_argument("--solvers", default="bfs", help="comma-separated")
    w.add_argument("--delay", type=float, default=0.005, help="seconds between events")
    w.add_argument("--race", action="store_true", help="side-by-side solver race")
    _server_args(w)
    w.set_defaults(func=cmd_watch)

    sv = sub.add_parser("serve", help="web viewer: replays, live runs, results dashboard")
    _server_args(sv)
    sv.set_defaults(func=cmd_serve)

    u = sub.add_parser("uniformity", help="chi-squared test: is a generator uniform?")
    u.add_argument("-g", "--generator", default="wilson")
    u.add_argument("-t", "--topology", default="square")
    u.add_argument("-s", "--size", type=int, nargs="+", default=[3, 3])
    u.add_argument("--samples", type=int, default=5000)
    u.add_argument("--seed", type=int, default=0)
    u.set_defaults(func=cmd_uniformity)
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (ValueError, NotImplementedError) as e:
        raise SystemExit(f"error: {e}")


if __name__ == "__main__":
    main()
