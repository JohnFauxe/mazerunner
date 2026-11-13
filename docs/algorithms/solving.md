# Maze Solving Algorithms — Research Notes

> **TL;DR** — Solvers come in two kinds. **Omniscient** solvers see the whole
> graph, are measured by CPU time and nodes expanded, and give optimal paths
> (BFS, Dijkstra, A*). **Agent** solvers only see their current cell and are
> measured by steps walked (wall follower, Trémaux, Pledge, random mouse).
> Wall following only works on simply connected (perfect) mazes and needs a
> planar neighbor order. Trémaux always terminates, even on braided mazes.

References
- **[TL]** W. D. Pullen, *Think Labyrinth: Maze Algorithms*. Its "solving algorithms" section covers random mouse, wall follower, Pledge, chain, Trémaux, dead-end filling, cul-de-sac filling, blind-alley filling, collision solver and shortest-path finders.
- **[HNR]** P. Hart, N. Nilsson, B. Raphael, "A Formal Basis for the Heuristic Determination of Minimum Cost Paths", IEEE TSSC 4(2), 1968 (A*).
- **[D]** E. W. Dijkstra, "A note on two problems in connexion with graphs", Numerische Math. 1, 1959.
- **[Lee]** C. Y. Lee, "An Algorithm for Path Connections and Its Applications", IRE Trans. Electronic Computers, 1961 (BFS wavefront on grids).
- **[Kf]** R. Korf, "Depth-first iterative-deepening", AI 27, 1985 (IDA*).
- **[HG]** D. Harabor, A. Grastien, "Online Graph Pruning for Pathfinding on Grid Maps", AAAI 2011 (JPS).
- **[Ab]** H. Abelson, A. diSessa, *Turtle Geometry*, MIT Press, 1980 (Pledge algorithm, attributed to John Pledge).
- **[Lu]** É. Lucas, *Récréations mathématiques*, 1882 (Trémaux's method).

## Comparison

| Algorithm | Mode | Optimal | Works on braided mazes | Memory | Needs |
|---|---|---|---|---|---|
| BFS / Lee | omniscient | yes (unweighted) | yes | O(n) | — |
| DFS | omniscient | no | yes (with visited set) | O(n) | — |
| Dijkstra | omniscient | yes (weighted) | yes | O(n) | — |
| A* | omniscient | yes (admissible h) | yes | O(n) | METRIC |
| Greedy best-first | omniscient | no | yes | O(n) | METRIC |
| Bidirectional BFS | omniscient | yes | yes | O(n) | — |
| IDA* | omniscient | yes | yes | O(depth) | METRIC |
| Dead-end filling | omniscient | yes on perfect mazes | partly (leaves loops) | O(n) | — |
| Jump Point Search | omniscient | yes | yes | O(n) | UNIFORM_GRID |
| Wall follower | agent | no | **no** (can loop around islands) | O(1) | PLANAR |
| Pledge | agent | no | escape-only (to the exterior) | O(1) | PLANAR, HEADINGS |
| Random mouse | agent | no | yes, eventually | O(1) | — |
| Trémaux | agent | no | **yes**, always terminates | marks on passages | — |
| Chain | agent | no | yes | O(n) | METRIC |

## Heuristics per topology (for A*, Greedy, IDA*)
- **Square:** Manhattan distance (admissible with 4-connectivity).
- **Hex:** cube/axial distance `(|dq| + |dr| + |ds|) / 2`.
- **Polar:** there is no simple exact metric, because cells widen with ring index. An admissible
  bound is `|Δring|`, and a tighter one adds the angular arc on the inner ring. Benchmarking how much
  heuristic quality matters is an interesting experiment in itself.
- **Fallback:** `h = 0`, which reduces A* to Dijkstra. This lets A* run (degraded) on topologies without METRIC.

## Agent sandbox contract
An agent gets a `Probe`: `here`, `exits()` (in cyclic order if PLANAR),
`move(cell)`, `at_goal()`, and for Trémaux `mark(edge)` and `marks(edge)`. Every call is
counted. A step budget (default `10 * n`) turns infinite loops into a recorded
`TIMEOUT` instead of a hang.
