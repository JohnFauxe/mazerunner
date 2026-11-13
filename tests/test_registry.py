from pathlib import Path

from mazerunner.bench.matrix import expand, load_config
from mazerunner.core.registry import generators, load_all, solvers, topologies
from mazerunner.core.traits import Trait

load_all()


def test_core_algorithms_registered():
    for k in ("recursive-backtracker", "wilson", "aldous-broder", "binary-tree", "eller"):
        assert k in generators
    for k in ("bfs", "astar", "wall-follower", "tremaux", "pledge"):
        assert k in solvers
    for k in ("square", "polar", "hex"):
        assert k in topologies


def test_binary_tree_skipped_on_hex_and_polar():
    trials, skips = expand(load_config(Path("benchmarks/configs/default.toml")))
    skipped = {(s.topology, s.algorithm) for s in skips}
    assert ("hex", "binary-tree") in skipped
    assert ("polar", "recursive-division") in skipped
    assert not any(t.topology == "hex" and t.generator == "binary-tree" for t in trials)


def test_seeds_are_independent_of_solver():
    trials, _ = expand(load_config(Path("benchmarks/configs/default.toml")))
    t0 = [t for t in trials if t.topology == "square" and t.generator == "wilson" and t.trial == 0
          and t.size == (10, 10)]
    assert len({t.seed for t in t0}) == 1 and len(t0) > 1


def test_square_has_every_planar_trait():
    sq = topologies.get("square").obj
    assert {Trait.ORTHOGONAL, Trait.PLANAR, Trait.METRIC} <= sq.traits
