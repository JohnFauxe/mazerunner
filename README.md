<img src="assets/icon.svg" width="64" height="64" alt="">

# MazeRunner

Benchmark harness for maze **generation** and **solving** algorithms across
square, round (polar) and hexagonal mazes, with more topologies planned.

- Plan & roadmap: [PLAN.md](PLAN.md)
- Algorithm research: [docs/algorithms/](docs/algorithms/)

```bash
uv sync
uv run mazerunner list                                   # registered algorithms + status
uv run mazerunner bench benchmarks/configs/default.toml --dry-run
uv run pytest
```

Created in [T3 Code](https://t3.codes).
