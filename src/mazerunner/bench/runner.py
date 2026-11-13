"""Execute trials: build topology, generate (cached per maze seed), validate,
solve, time, record. Phase 1.

Design notes
- Timing: time.perf_counter_ns, `warmup` + `repeats` from config, report median.
- Memory: tracemalloc peak, measured on a separate run so it doesn't skew timing.
- Same maze for every solver: the generation seed excludes the solver key.
- Optional subprocess isolation (placeholder) for clean memory numbers.
"""

from mazerunner.bench.matrix import Trial


def run_trial(trial: Trial, *, warmup: int = 1, repeats: int = 5) -> dict:
    raise NotImplementedError("bench runner: phase 1")


def run(trials: list[Trial], out_path, **kw) -> None:
    raise NotImplementedError("bench runner: phase 1")
