"""Expand a benchmark config into concrete trials, filtering by traits (PLAN §4)."""

from __future__ import annotations

import itertools
import tomllib
from dataclasses import dataclass
from pathlib import Path

from mazerunner.core.registry import generators, load_all, solvers, topologies


@dataclass(frozen=True)
class Trial:
    topology: str
    size: tuple[int, ...]
    generator: str
    solver: str
    braid: float
    trial: int
    seed: int


@dataclass(frozen=True)
class Skip:
    topology: str
    algorithm: str
    reason: str


def load_config(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def expand(cfg: dict) -> tuple[list[Trial], list[Skip]]:
    """Cartesian product of the config, dropping trait-incompatible pairs."""
    load_all()
    trials, skips = [], []
    seed = cfg.get("seed", 0)
    for topo_cfg in cfg["topology"]:
        tkey = topo_cfg["name"]
        tcls = topologies.get(tkey).obj
        traits = tcls.traits
        gens, sols = [], []
        for g in cfg["generators"]:
            ok, missing = generators.get(g).compatible(traits)
            (gens.append(g) if ok else skips.append(Skip(tkey, g, f"missing {sorted(t.name for t in missing)}")))
        for s in cfg["solvers"]:
            ok, missing = solvers.get(s).compatible(traits)
            (sols.append(s) if ok else skips.append(Skip(tkey, s, f"missing {sorted(t.name for t in missing)}")))
        for size, g, s, b, i in itertools.product(
            [tuple(x) for x in topo_cfg["sizes"]], gens, sols,
            cfg.get("braid", [0.0]), range(cfg.get("trials", 1)),
        ):
            from mazerunner.core.rng import derive_seed
            trials.append(Trial(tkey, size, g, s, b, i, derive_seed(seed, tkey, size, g, b, i)))
    return trials, skips
