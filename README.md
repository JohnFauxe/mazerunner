<img src="assets/icon.svg" width="64" height="64" alt="">

# MazeRunner

A benchmark harness for maze **generation** and **solving** algorithms on
square, round (polar) and hexagonal mazes. You can watch any run step by step,
live or as a replay.

- Plan, design and roadmap: [PLAN.md](PLAN.md)
- Algorithm research notes: [docs/algorithms/](docs/algorithms/)

## Quick start

```bash
uv sync
uv run mazerunner list                                     # what's implemented, with trait requirements

# one maze
uv run mazerunner generate -t square -s 12 20 -g wilson --ascii --unicode
uv run mazerunner generate -t polar -s 10 -g kruskal --svg polar.svg
uv run mazerunner solve -t hex -s 15 15 -g eller --solver astar --svg hex.svg

# watch it
uv run mazerunner serve                                    # web viewer: Run / Race / Traces / Results
uv run mazerunner watch -t hex -s 15 15 -g wilson --solvers astar,tremaux
uv run mazerunner watch -t polar -s 12 -g prim-simplified --solvers bfs,astar,wall-follower --race
uv run mazerunner record -t square -s 20 20 -g recursive-division --solver tremaux
uv run mazerunner replay traces/<file>.trace.jsonl         # in the terminal (square), or --web, or --svg out.svg

# benchmark
uv run mazerunner bench benchmarks/configs/smoke.toml --out results/smoke.jsonl
uv run mazerunner report results/smoke.jsonl               # results/report/summary.md (+ PNG charts with the `report` extra)
uv run mazerunner uniformity -g wilson                     # chi-squared: does the generator produce every maze equally often?

uv run pytest
```

Start and goal default to **opposite sides**. Change this with `--placement`
(`opposite-sides`, `corners`, `diameter`, `center-out`, `random`), `--side`
(which pair of sides) and `--along` (`center` or `random`). In configs, use the `[endpoints]` table.

Created in [T3 Code](https://t3.codes).
