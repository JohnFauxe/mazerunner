"""High-level entry points shared by the CLI, bench runner and viewer.

    topo = make_topology("square", (20, 20))
    maze = generate(topo, "wilson", seed=1, endpoints={"placement": "opposite-sides"})
    result = solve(maze, "astar", seed=1)
    path = record("hex", (10, 10), "wilson", "astar", seed=1, out=Path("traces/x.trace.jsonl"))
"""

from __future__ import annotations

import random
from pathlib import Path

from mazerunner.core.endpoints import DEFAULT, place
from mazerunner.core.maze import Maze
from mazerunner.core.registry import generators, load_all, solvers, topologies
from mazerunner.core.rng import derive_seed
from mazerunner.core.topology import Topology
from mazerunner.core.trace import NULL, Recorder, Tracer

load_all()


def make_topology(name: str, size: tuple | list, **kw) -> Topology:
    return topologies.get(name).obj(*size, **kw)


def generate(topology: Topology, generator: str, seed: int, *, params: dict | None = None,
             endpoints: dict | None = None, braid: float = 0.0, tracer: Tracer = NULL) -> Maze:
    """Carve → braid (optional) → place endpoints. Deterministic in `seed`."""
    info = generators.get(generator)
    ok, missing = info.compatible(topology.traits)
    if not ok:
        raise ValueError(f"{generator} needs {sorted(t.name for t in missing)} "
                         f"which {topology.name} lacks")
    rng = random.Random(seed)
    gen = info.obj(**(params or {}))
    tracer.emit("phase", label=f"generate: {generator}")
    maze = gen.generate(topology, rng, tracer=tracer)
    if braid > 0:
        from mazerunner.generators.braid import braid as do_braid
        tracer.emit("phase", label=f"braid {braid}")
        do_braid(maze, braid, random.Random(derive_seed(seed, "braid")))
    ep = dict(endpoints or {})
    place(maze, ep.pop("placement", DEFAULT), random.Random(derive_seed(seed, "endpoints")), **ep)
    maze.meta.update(seed=seed, braid=braid)
    return maze


def solve(maze: Maze, solver: str, seed: int = 0, *, params: dict | None = None,
          tracer: Tracer = NULL):
    info = solvers.get(solver)
    ok, missing = info.compatible(maze.topology.traits)
    if not ok:
        raise ValueError(f"{solver} needs {sorted(t.name for t in missing)}")
    s = info.obj(**(params or {}))
    s.tracer = tracer
    tracer.emit("phase", label=f"solve: {solver}")
    old, maze.tracer = maze.tracer, tracer
    try:
        result = s.solve(maze, random.Random(derive_seed(seed, "solve", solver)))
    finally:
        maze.tracer = old
    if result.path:
        tracer.emit("path", *result.path)
    return result


def trace_header(topology: Topology, **extra) -> dict:
    return {"topology": topology.describe(), "geometry": topology.geometry(), **extra}


def record(topology: str, size, generator: str, solver: str | None, seed: int, out: Path, *,
           gen_params=None, solver_params=None, endpoints=None, braid: float = 0.0) -> Path:
    """Run once with a Recorder and write a replayable .trace.jsonl."""
    topo = make_topology(topology, size)
    rec = Recorder(topo.index, trace_header(topo, generator=generator, solver=solver, seed=seed,
                                            braid=braid, endpoints=endpoints or {}))
    maze = generate(topo, generator, seed, params=gen_params, endpoints=endpoints,
                    braid=braid, tracer=rec)
    footer = {"maze": {"links": maze.n_links, "start": topo.index[maze.start],
                       "goal": topo.index[maze.goal]}}
    if solver:
        r = solve(maze, solver, seed, params=solver_params, tracer=rec)
        footer["result"] = {"outcome": r.outcome.value, "path_len": len(r.path),
                            "counters": r.counters, "optimal": maze.shortest_path_length()}
    rec.footer = footer
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fp:
        rec.dump(fp)
    return out
