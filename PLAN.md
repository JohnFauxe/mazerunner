# MazeRunner — Project Plan

> **TL;DR** — A Python 3.12 benchmarking harness for maze *generation* and maze
> *solving* algorithms. Every maze is a graph of cells over a pluggable
> **topology** (square, polar/round, hex, later triangle/upsilon/weave/3D).
> Algorithms declare the topology **traits** they need, so the benchmark matrix
> automatically skips impossible pairings (e.g. Binary Tree on a hex grid).
> Every run can be **watched step by step**, live or as a replay, in a local
> web viewer that also hosts the results dashboard.
> All algorithms are well-known published ones — see
> [`docs/algorithms/`](docs/algorithms/) — nothing is invented.

---

## 1. Goals

1. Generate mazes with any established algorithm on any supported topology.
2. Solve them with any established algorithm, in two modes:
   - **Omniscient** — the solver sees the whole graph (BFS, A*, …).
   - **Agent** — the solver only sees the cell it is standing in (wall
     follower, Pledge, Trémaux, …). This is what a "maze runner" actually does.
3. Benchmark both, reproducibly (seeded), and report:
   - generation cost and the *character* of the maze produced (texture metrics),
   - solver cost (time, nodes expanded, steps walked) and path quality.
4. Let a human **watch** any generation or solve step by step, live or replayed.
5. Make adding a topology, generator, solver or metric a single-file change.

### Non-goals (for now)
- A game. (The viewer is for watching and comparing algorithms.)
- Inventing new algorithms. We implement published ones faithfully and cite them.

---

## 2. Core design

### 2.1 Everything is a graph

Following the architecture in Jamis Buck's *Mazes for Programmers* (2015):

```
Topology  ── defines cells + which cells are *adjacent* (potential passages)
   │
Maze      ── Topology + the set of *links* (carved passages) + start/goal
   │
Generator ── decides which adjacencies become links
Solver    ── finds a route through the links
```

A **cell** is an opaque hashable id (a tuple such as `(row, col)` or
`(ring, index)`). Generators and solvers that only need `neighbors(cell)` work
on every topology for free. Most of the classic algorithms are actually
"build a spanning tree of a graph", so they are topology-agnostic.

### 2.2 Topology traits (capability model)

Some algorithms rely on geometry, not just the graph. Each topology declares
traits; each algorithm declares the traits it requires.

| Trait            | Meaning                                                         | Needed by                           |
|------------------|-----------------------------------------------------------------|-------------------------------------|
| `ROWS`           | Cells are arranged in ordered rows/rings                        | Sidewinder, Eller's                 |
| `ORTHOGONAL`     | Each cell has well-defined "north" and "east" style axes        | Binary Tree                         |
| `RECTANGULAR`    | Area can be split by straight walls into sub-rectangles         | Recursive Division                  |
| `PLANAR`         | Embeds in the plane with a consistent cyclic neighbor order     | Wall follower, Pledge               |
| `HEADINGS`       | Absolute headings exist (needed to count turns)                 | Pledge                              |
| `METRIC`         | Cells have coordinates; an admissible distance heuristic exists | A*, Greedy best-first, IDA*         |
| `UNIFORM_GRID`   | Square lattice with uniform cost                                | Jump Point Search                   |
| `WEAVE`          | Passages may cross over/under                                   | (topology feature, affects renderers) |

The benchmark matrix intersects these, so an incompatible pair is reported as
`skipped: missing trait X` instead of crashing.

### 2.3 Topologies

| Topology              | Status    | Notes                                                                 |
|-----------------------|-----------|-----------------------------------------------------------------------|
| **Square** (orthogonal) | Phase 1 | Reference topology. Traits: all except WEAVE.                         |
| **Polar** (round)     | Phase 2   | Rings of cells; outer rings subdivide to keep cell size even (Buck ch. 7). Traits: ROWS, PLANAR, HEADINGS, METRIC. |
| **Hex** (sigma)       | Phase 2   | Axial/offset coordinates, 6 neighbors. Traits: ROWS, PLANAR, HEADINGS, METRIC. |
| Triangle (delta)      | Placeholder | Alternating up/down triangles, 3 neighbors.                         |
| Upsilon (octagon+square) | Placeholder | Mixed degree 8/4.                                                |
| Weave                 | Placeholder | Square + over/under crossings (Buck ch. 9).                         |
| 3D / multi-level      | Placeholder | Stacked grids with up/down links (Buck ch. 13).                     |
| Arbitrary graph / masked | Placeholder | Image-masked shapes, Voronoi cells.                              |

Terminology (orthogonal / delta / sigma / theta / upsilon) follows Walter
Pullen, *Think Labyrinth: Maze Algorithms*.

### 2.4 Generators

Full research notes: [`docs/algorithms/generation.md`](docs/algorithms/generation.md).

| Algorithm                     | Family              | Requires     | Phase |
|-------------------------------|---------------------|--------------|-------|
| Recursive Backtracker (DFS)   | Random walk / stack | —            | 1     |
| Binary Tree                   | Per-cell coin flip  | ORTHOGONAL   | 1     |
| Sidewinder                    | Per-row runs        | ROWS         | 1     |
| Aldous–Broder                 | Uniform spanning tree | —          | 1     |
| Wilson's                      | Uniform spanning tree (LERW) | —   | 1     |
| Hunt-and-Kill                 | Random walk + scan  | —            | 2     |
| Randomized Prim's (simplified & true) | MST         | —            | 2     |
| Randomized Kruskal's          | MST / union-find    | —            | 2     |
| Growing Tree (pluggable pick strategy) | Generalises DFS/Prim | — | 2     |
| Eller's                       | Row-at-a-time sets  | ROWS         | 3     |
| Recursive Division            | Wall-adding         | RECTANGULAR  | 3     |
| Cellular automaton (Maze/Mazectric rules) | CA, non-perfect | ORTHOGONAL | Placeholder |
| Braiding post-process (remove dead ends) | Modifier   | —            | Placeholder |

### 2.5 Solvers

Full research notes: [`docs/algorithms/solving.md`](docs/algorithms/solving.md).

| Algorithm               | Mode        | Requires    | Optimal? | Phase |
|-------------------------|-------------|-------------|----------|-------|
| Breadth-first search    | Omniscient  | —           | Yes (unweighted) | 1 |
| Depth-first search      | Omniscient  | —           | No       | 1 |
| Dijkstra                | Omniscient  | —           | Yes      | 1 |
| A*                      | Omniscient  | METRIC      | Yes (admissible h) | 1 |
| Greedy best-first       | Omniscient  | METRIC      | No       | 2 |
| Bidirectional BFS       | Omniscient  | —           | Yes      | 2 |
| Dead-end filling        | Omniscient  | —           | Yes on perfect mazes | 2 |
| IDA*                    | Omniscient  | METRIC      | Yes      | 3 |
| Jump Point Search       | Omniscient  | UNIFORM_GRID| Yes      | Placeholder |
| Wall follower (left/right) | Agent    | PLANAR      | No; fails if goal is inside an island | 1 |
| Random mouse            | Agent       | —           | No       | 1 |
| Trémaux's               | Agent       | —           | No; always terminates | 2 |
| Pledge                  | Agent       | PLANAR, HEADINGS | No (escape-only) | 3 |
| Chain algorithm         | Agent       | METRIC      | No       | Placeholder |

### 2.6 Agent sandbox

Agent solvers receive a `Probe` instead of the `Maze`. It exposes only the
current cell, the passages out of it (in cyclic order, if PLANAR), and
optional chalk marks (for Trémaux). Every call is counted. That's how we
benchmark them fairly: their cost is **steps walked**, not CPU time.

### 2.7 Start/goal placement

Placement is a generation option, so it is recorded in the maze's metadata and
is a benchmark dimension. Code: `core/endpoints.py`.

| Placement | Meaning | Default? |
|---|---|---|
| `opposite-sides` | Two boundary cells half a perimeter apart | **yes** |
| `corners` | First and last cell (square: NW→SE) | |
| `diameter` | The two cells with the longest shortest path between them (computed after carving) | |
| `center-out` | Centre cell → boundary (natural for polar) | |
| `random` | Two random cells (seeded) | |
| `manual` | Explicit `start` / `goal` cells | |

`opposite-sides` is generic. Each topology lists its boundary cells in cyclic
order (`Topology.boundary()`). Options: `side` picks which pair of sides as a
fraction of the perimeter (square: `0.0` = west→east, `0.25` = north→south);
`along = "center" | "random"` picks the cell along that side.
Square: middle of west edge → middle of east edge. Polar: two opposite
outer-ring cells. Hex: opposite edges.

### 2.8 Weighted mazes *(planned now, built in Phase 4)*

`Maze.weights` holds an optional per-cell traversal cost. Weight sources:
uniform (the default, same as unweighted), random range, noise field, image.
Every interface already carries the field, so adding weights later doesn't
change any algorithm signatures. Once weights exist, Dijkstra and A* give
different results from BFS, and "optimal" means cheapest rather than shortest. Placeholder: `core/weights.py`.

---

## 3. Metrics

### 3.1 Maze texture (from the generator's output)
- Dead-end count / ratio
- Junction counts by degree (2-way corridors, 3-way, 4-way, …)
- Average corridor length (the "river" factor)
- Diameter: the longest shortest path (two BFS passes on a tree)
- Solution length between the chosen start and goal; tortuosity = solution length / straight-line distance
- Directional bias (share of horizontal vs vertical passages; diagonal bias for Binary Tree)
- Perfect-maze check: spanning tree ⇔ connected and |links| = |cells| − 1
- Uniformity check (statistical): for tiny grids, enumerate all spanning trees
  and run a chi-squared test on generator output. This checks that Aldous–Broder
  and Wilson's are uniform, and shows how far DFS, Prim and the others are from uniform.

### 3.2 Generation cost
- Wall-clock (`time.perf_counter_ns`), median over N repeats after warm-up
- Peak memory (`tracemalloc`)
- Algorithm-specific counters (e.g. random-walk steps for Aldous–Broder)

### 3.3 Solver cost and quality
- Wall-clock, peak memory
- Nodes expanded / frontier max size (omniscient)
- Steps walked, revisits, probes (agent)
- Path length vs optimal (BFS ground truth) → **optimality ratio**
- Success / failure / timeout (agents can loop forever without a step budget)

---

## 4. Benchmark harness

```
benchmarks/configs/*.toml  ──►  Matrix expander  ──►  Runner  ──►  results/*.jsonl  ──►  Report
  topology × size ×             (filters by traits,    (seeded,       (one row per         (tables,
  generator × solver × seeds     records skips)         isolated)      trial)               charts, HTML)
```

- **Reproducible:** each trial gets `seed = hash(config_seed, topology, size, generator, trial_index)`.
  The same maze is reused for every solver, so solver comparisons run on identical mazes.
- **Isolation:** optional subprocess-per-trial mode for memory measurement.
- **Output:** JSON Lines (append-only, easy to resume), loadable into pandas/polars.
- **Validation:** before a result counts, the maze must be checked by `validate()`
  (perfect if the generator claims perfect) and the path checked by `verify_path()`.
- **Cross-check:** `networkx` is a test-only dependency, used for ground truth
  (connectivity, spanning-tree check, shortest-path length).

---

## 5. Watching: live view, replay and results dashboard

### 5.1 Tracing
Algorithms don't draw. They emit small events into a `Tracer` (`core/trace.py`):

- Generation: `carve`, `uncarve`, `wall`, `current`, `frontier_add/remove`, `walk`, `erase` (Wilson's loop erasure), `set_merge`, `phase`
- Solving: `visit`, `frontier_add/remove`, `current`, `move` (agents), `mark` (Trémaux), `fill`, `path`

`Maze.link()` emits `carve` automatically and the agent `Probe` emits `move`
and `mark`, so most algorithms get basic tracing for free and add only the
extra events specific to them.

**Timing stays clean.** Benchmarks run with the no-op `NULL` tracer. A trace
comes from a *separate* run with the same seed, so the replay matches the
benchmarked run exactly without its overhead being measured. A test (Phase 1)
will check that the no-op tracer adds only negligible time.

### 5.2 Trace format (`.trace.jsonl`)
```
{"type":"header","version":1,"topology":"polar","args":[25],"seed":…,
 "generator":"wilson","solver":"astar","start":12,"goal":907,
 "geometry":{"cells":[…polygons or arcs…]}}
[0,"carve",[0,1]]
[1,"walk",[1]]
[2,"frontier_add",[5],{"f":14}]
```
Cells are written as integer indexes, which keeps files compact. The header carries the drawable
geometry, so the viewer doesn't need to know anything about square, polar or hex topologies.

### 5.3 Viewer (`mazerunner serve`)
A local web app served by the Python standard library (`http.server` plus Server-Sent Events, no extra dependencies):

- **Replay:** open any trace. Play, pause, step forward/back, scrub, change speed, jump to a phase.
- **Live:** `mazerunner watch --topology hex --gen wilson --solver astar` runs the algorithm with a streaming tracer and pushes each event as it happens, with an adjustable delay.
- **Race mode:** several solvers on the *same* maze, side by side, in lockstep. This shows BFS against A* against the wall follower directly.
- **Counters panel:** frontier size, nodes expanded and steps walked, updated live.
- **Results dashboard** (Phase 3): charts from the benchmark JSONL. Click a trial to replay it.

A cheap **terminal player** for square mazes (ANSI redraw) comes first in Phase 1, so watching works before the web viewer exists.

---

## 6. Project layout

```
mazerunner/
├── PLAN.md                     ← this file
├── pyproject.toml              ← uv-managed, Python ≥ 3.12
├── docs/algorithms/            ← research notes & references
│   ├── generation.md
│   ├── solving.md
│   └── topologies.md
├── benchmarks/configs/         ← benchmark matrix definitions (TOML)
├── src/mazerunner/
│   ├── core/                   ← Topology ABC, traits, Maze, registry, RNG,
│   │                              endpoints, trace, weights (planned)
│   ├── topologies/             ← square, polar, hex (+ placeholders)
│   ├── generators/             ← one file per algorithm
│   ├── solvers/                ← one file per algorithm (omniscient + agent)
│   ├── metrics/                ← texture metrics, solve metrics, uniformity
│   ├── bench/                  ← matrix expansion, runner, results store, report
│   ├── render/                 ← ASCII (square), SVG (all topologies), animation (placeholder)
│   ├── io/                     ← maze serialisation (JSON)
│   ├── viewer/                 ← web viewer server + static app, terminal player
│   └── cli.py                  ← `mazerunner list | generate | solve | bench | report |
│                                   record | replay | watch | serve`
├── traces/                     ← recorded .trace.jsonl files (git-ignored)
└── tests/
```

---

## 7. Roadmap

| Phase | Deliverable | Exit criteria |
|-------|-------------|---------------|
| **0 — Skeleton** *(done)* | Package layout, ABCs, registry, trait model, stubs, CLI `list` | `uv run mazerunner list` shows every algorithm and its phase |
| **1 — Square MVP** | SquareGrid; DFS, Binary Tree, Sidewinder, Aldous–Broder, Wilson's; BFS, DFS, Dijkstra, A*, wall follower, random mouse; endpoint placements (opposite-sides, corners, random, manual, diameter); ASCII render; trace recording; terminal replay; validation; basic runner | Benchmark a 4×4 to 200×200 matrix end-to-end; all mazes validate; property tests pass |
| **2 — Round & Hex** | PolarGrid, HexGrid; SVG renderer; **web viewer: replay + live + race mode**; `center-out` placement; Hunt-and-Kill, Prim's, Kruskal's, Growing Tree; Greedy, Bidirectional BFS, dead-end filling, Trémaux | Same benchmark suite runs on all three topologies |
| **3 — Analysis** | Texture metrics, uniformity test, Eller's, Recursive Division, IDA*, Pledge; **results dashboard in the viewer** (click a trial to replay it) | Report compares generators by texture and solvers by cost |
| **4 — Extensions** | **Weighted mazes**; placeholders → real: triangle, upsilon, weave, 3D, masks, braiding, CA, JPS, chain, animation, optional Rust/numba fast paths | Driven by interest |

---

## 8. Key decisions & rationale

- **Python first.** Readability and fast iteration matter more than raw speed
  for a comparative benchmark: every algorithm pays the same interpreter tax.
  The relative rankings hold. A compiled backend is a Phase 4 placeholder, behind the same interfaces.
- **Pure-Python core, no heavy dependencies.** `networkx` is used for test
  validation only, so its implementation doesn't skew the timings.
  Rendering uses plain SVG text.
- **Links stored as a set of frozen pairs on the Maze, not on cells.** This keeps
  the Topology immutable and shareable across trials, and makes "same maze, many solvers" cheap.
- **Agent solvers are sandboxed**, so they can't cheat by reading the whole graph.
- **Tracing is separate from timing.** Replays come from an untimed run with the same seed.
- **Weighted mazes:** planned in the interfaces now, built in Phase 4. *(decided 2026-11-13)*
- **Default endpoints = opposite sides**, configurable per run. *(decided 2026-11-13)*
- **Web viewer for watching and results: yes.** *(decided 2026-11-13)*

## 9. Open questions

1. Viewer front-end: plain JS modules (no build step), or a small TypeScript build? The plan assumes plain JS for zero tooling.
2. Should live mode let you *edit* the maze mid-run (toggle walls) to probe solver behaviour? Not planned, but the event model allows it.
