"""Expand a benchmark config into concrete trials, filtering by traits (PLAN §4)."""

from __future__ import annotations

import itertools
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from mazerunner.core.registry import generators, load_all, solvers, topologies
from mazerunner.core.rng import derive_seed


@dataclass(frozen=True)
class Trial:
    topology: str
    size: tuple[int, ...]
    generator: str
    solver: str
    braid: float
    trial: int
    seed: int

    @property
    def maze_key(self) -> tuple:
        """Trials sharing this key share one maze (solver excluded)."""
        return (self.topology, self.size, self.generator, self.braid, self.trial, self.seed)


@dataclass(frozen=True)
class Skip:
    topology: str
    algorithm: str
    reason: str


@dataclass
class RunSettings:
    """Per-run knobs from the config: endpoints, timing, tracing."""
    endpoints: dict = field(default_factory=dict)  # kwargs for api.generate(endpoints=...)
    warmup: int = 1
    repeats: int = 5
    trace_record: bool = False
    trace_sample: int = 1
    trace_dir: str = "traces"

    @property
    def placement(self) -> str:
        return self.endpoints.get("placement", "opposite-sides")

    @classmethod
    def from_config(cls, cfg: dict) -> "RunSettings":
        tr = cfg.get("trace", {})
        return cls(
            endpoints=dict(cfg.get("endpoints", {})),
            warmup=int(cfg.get("warmup", 1)),
            repeats=max(1, int(cfg.get("repeats", 5))),
            trace_record=bool(tr.get("record", False)),
            trace_sample=int(tr.get("sample", 1)),
            trace_dir=str(tr.get("dir", "traces")),
        )


def load_config(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _missing(missing) -> str:
    return f"missing {sorted(t.name for t in missing)}"


def expand(cfg: dict) -> tuple[list[Trial], list[Skip]]:
    """Cartesian product of the config, dropping trait-incompatible pairs,
    unimplemented algorithms and topologies that cannot be constructed."""
    load_all()
    trials, skips = [], []
    seed = cfg.get("seed", 0)
    for topo_cfg in cfg["topology"]:
        tkey = topo_cfg["name"]
        tcls = topologies.get(tkey).obj
        traits = tcls.traits
        sizes = [tuple(x) for x in topo_cfg["sizes"]]
        gens, sols = [], []
        for kind, keys, reg, out in (("g", cfg["generators"], generators, gens),
                                     ("s", cfg["solvers"], solvers, sols)):
            for k in keys:
                info = reg.get(k)
                ok, missing = info.compatible(traits)
                if not ok:
                    skips.append(Skip(tkey, k, _missing(missing)))
                elif not info.implemented:
                    skips.append(Skip(tkey, k, "not implemented"))
                else:
                    out.append(k)
        try:
            if sizes:
                tcls(*sizes[0])
        except NotImplementedError:
            skips.append(Skip(tkey, "*", "not implemented"))
            continue
        for size, g, s, b, i in itertools.product(
            sizes, gens, sols, cfg.get("braid", [0.0]), range(cfg.get("trials", 1)),
        ):
            trials.append(Trial(tkey, size, g, s, b, i, derive_seed(seed, tkey, size, g, b, i)))
    return trials, skips
