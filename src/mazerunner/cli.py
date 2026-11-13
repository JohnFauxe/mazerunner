"""mazerunner CLI: list | generate | solve | bench | report."""

from __future__ import annotations

import argparse
from pathlib import Path

from mazerunner.core.registry import generators, load_all, solvers, topologies


def cmd_list(_args) -> None:
    load_all()
    for reg in (topologies, generators, solvers):
        print(f"\n{reg.kind.upper().replace('Y', 'IE')}S")
        for i in reg.all():
            status = "ready" if i.implemented else f"phase {i.phase.value}"
            if reg is topologies:
                req = "has=" + ",".join(sorted(t.name for t in i.obj.traits))
            else:
                req = "needs=" + (",".join(sorted(t.name for t in i.requires)) or "-")
            tags = ",".join(sorted(i.tags))
            print(f"  {i.key:22} {status:9} {req:34} {tags}")


def cmd_bench(args) -> None:
    from mazerunner.bench.matrix import expand, load_config
    trials, skips = expand(load_config(Path(args.config)))
    print(f"{len(trials)} trials, {len(skips)} skipped pairings")
    for s in skips:
        print(f"  skip {s.topology:8} {s.algorithm:22} {s.reason}")
    if args.dry_run:
        return
    from mazerunner.bench.runner import run
    run(trials, Path(args.out))


def _todo(name):
    def f(_args):
        raise SystemExit(f"`{name}` is not implemented yet (see PLAN.md roadmap)")
    return f


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="mazerunner")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="show registered topologies and algorithms").set_defaults(func=cmd_list)
    b = sub.add_parser("bench", help="run a benchmark matrix")
    b.add_argument("config")
    b.add_argument("--out", default="results/results.jsonl")
    b.add_argument("--dry-run", action="store_true")
    b.set_defaults(func=cmd_bench)
    for name, help_ in (
        ("generate", "generate one maze (--endpoints opposite-sides|corners|diameter|center-out|random|manual)"),
        ("solve", "solve a saved maze"),
        ("report", "summarise benchmark results"),
        ("record", "run generator+solver once with tracing and save a .trace.jsonl"),
        ("replay", "replay a .trace.jsonl (terminal for square, or opens the web viewer)"),
        ("watch", "run live and watch step by step in the web viewer"),
        ("serve", "start the web viewer (replays, live runs, results dashboard)"),
    ):
        sub.add_parser(name, help=f"(planned) {help_}").set_defaults(func=_todo(name))
    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
