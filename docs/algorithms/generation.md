# Maze Generation Algorithms — Research Notes

> **TL;DR** — Almost every classic generator builds a *random spanning tree*
> of the cell graph (a "perfect" maze: exactly one path between any two cells).
> They differ in **bias**, which is the texture they produce. Aldous–Broder and Wilson's
> are the only ones here that are *uniform* (every spanning tree equally likely).
> DFS gives long winding corridors. Prim's gives many short dead ends. Binary
> Tree and Sidewinder are fast but leave visible diagonal or row artefacts. Only
> Binary Tree, Sidewinder, Eller's and Recursive Division depend on grid
> geometry. The rest run on any topology.

Primary references
- **[MfP]** Jamis Buck, *Mazes for Programmers*, Pragmatic Bookshelf, 2015.
- **[JB-blog]** Jamis Buck, "Maze Generation" blog series (weblog.jamisbuck.org, 2010–2011), with an algorithm-by-algorithm walkthrough.
- **[TL]** Walter D. Pullen, *Think Labyrinth: Maze Algorithms* (astrolog.org/labyrnth/algrithm.htm). This is the standard taxonomy and comparison table.
- **[AB]** D. Aldous, "The random walk construction of uniform spanning trees", SIAM J. Discrete Math 3(4), 1990; A. Broder, "Generating random spanning trees", FOCS 1989.
- **[W]** D. B. Wilson, "Generating random spanning trees more quickly than the cover time", STOC 1996.
- **[K]** J. B. Kruskal, "On the shortest spanning subtree of a graph", Proc. AMS 7, 1956.
- **[P]** R. C. Prim, "Shortest connection networks and some generalizations", Bell Syst. Tech. J. 36, 1957 (Jarník 1930).
- **[E]** Marlin Eller, 1982. The algorithm is documented in [TL] and [JB-blog].

Throughout, *n* = number of cells.

---

## 1. Comparison table

| Algorithm | Time | Extra memory | Uniform? | Bias / texture | Topology needs | Perfect? |
|---|---|---|---|---|---|---|
| Recursive Backtracker (DFS) | O(n) | O(n) stack | No | Long, twisty corridors; few dead ends; high "river" | any graph | yes |
| Binary Tree | O(n) | O(1) | No | Strong diagonal bias; two edges are unbroken corridors | ORTHOGONAL | yes |
| Sidewinder | O(n) | O(row) | No | Top row is one corridor; vertical bias upward | ROWS | yes |
| Aldous–Broder | O(cover time), roughly O(n log n) to O(n²) | O(1) | **Yes** | Unbiased | any graph | yes |
| Wilson's | O(mean hitting time), usually faster than A–B | O(n) | **Yes** | Unbiased | any graph | yes |
| Hunt-and-Kill | O(n²) worst case (the scan) | O(1) | No | Like DFS but fewer, longer corridors | any graph | yes |
| Prim's (simplified) | O(n log n) / O(n) | O(frontier) | No | Radial; many short dead ends | any graph | yes |
| Prim's (true, random weights) | O(E log E) | O(E) | No | Similar to Kruskal | any graph | yes |
| Kruskal's (randomized) | O(E α(n)) | O(n) union-find | No (close) | Many short dead ends, "patchy" | any graph | yes |
| Growing Tree | O(n) | O(n) | No | Tunable: newest = DFS, random = Prim, mixes in between | any graph | yes |
| Eller's | O(n) | O(width) | No | Similar to Kruskal; can produce infinite-height mazes | ROWS | yes |
| Recursive Division | O(n log n) | O(log n) stack | No | Long straight walls, box-like rooms | RECTANGULAR | yes |
| Cellular automaton (B3/S12345 "Maze") | O(n·gens) | O(n) | — | Organic, not a tree | ORTHOGONAL | **no** |

"Uniform" means every spanning tree of the grid graph is equally likely. We
check this empirically in `metrics/uniformity.py` (PLAN §3.1).

---

## 2. Algorithm notes

### 2.1 Recursive Backtracker (randomized depth-first search)
Start at a random cell. Repeatedly move to a random *unvisited* neighbor,
carving a passage and pushing onto a stack. When stuck, pop (backtrack). Done
when the stack is empty. Implement it with an **explicit stack**, because Python's
recursion limit breaks recursive versions on large grids. [MfP ch. 5], [TL]
- Texture: the longest corridors and fewest dead ends (~10% of cells) of the common algorithms.
- Works on any topology unchanged.

### 2.2 Binary Tree
For each cell, link it to either its north or its east neighbor, chosen at random
(on the top row or east column, take the only option). [MfP ch. 2]
- Stateless, so it can be streamed and parallelised.
- Bias: the north row and east column are always straight corridors, and there is a strong NE diagonal texture.
- Needs two orthogonal "forward" axes, so square only (triangle/hex variants exist but are not classic).

### 2.3 Sidewinder
Process rows. Keep a "run" of cells. At each cell, randomly either extend the run
east, or close it by linking one random cell of the run north. The top row is
one corridor. [MfP ch. 2]
- Needs ordered rows. Polar mazes have rings that can serve as rows (Buck shows polar variants), so polar gets trait `ROWS`.

### 2.4 Aldous–Broder
Random walk. Whenever the walk enters an unvisited cell, carve the edge it came
through. Stop when all cells are visited. [AB]
- **Produces a uniform spanning tree.**
- Very slow to finish: the last few unvisited cells take a long time to hit. This is a good benchmark case for the "cover time" cost.

### 2.5 Wilson's
Mark one cell as in the maze. From a random cell outside it, do a *loop-erased
random walk* until the walk hits the maze, then add that path. Repeat. [W]
- **Uniform spanning tree.** Slow at the start and fast at the end, the mirror image of Aldous–Broder.
- A known hybrid runs A–B first and switches to Wilson's (Buck mentions this). Kept as a **placeholder variant**.

### 2.6 Hunt-and-Kill
A random walk to unvisited neighbors (the "kill" phase). When stuck, scan the grid for
the first unvisited cell that is next to a visited one, link them, and resume
(the "hunt" phase). [MfP ch. 5]
- Like DFS but with no stack. The texture is similar, with somewhat longer corridors.
- The scan order needs a cell ordering. Every topology provides `cells()` in a deterministic order, so this works on any graph.

### 2.7 Prim's (randomized)
- *Simplified*: keep a set of "active" cells. Pick a random active cell. If it has an unvisited neighbor, link to one and add it to the set, else remove the cell.
- *True*: give every cell (or edge) a random weight, then run Prim's MST on those weights. [P]
- Texture: radiates from the start point, with lots of short dead ends (~30%+ dead ends on square grids).

### 2.8 Kruskal's (randomized)
Shuffle all candidate edges. For each one, if it joins two different sets
(union-find), carve it. [K]
- Natural fit for any graph. Union-find with path compression and union by rank gives near-linear time.
- Also the basis for weave mazes (pre-placing crossings) [MfP ch. 9], so it ties into the **weave placeholder**.

### 2.9 Growing Tree
A generalisation: keep a list of cells. Pick one with a strategy (`newest`,
`random`, `oldest`, `middle`, or mixes such as "newest 75% / random 25%"). Carve to an
unvisited neighbor or remove the cell. [JB-blog], [MfP ch. 11]
- `newest` gives DFS behaviour and `random` gives simplified-Prim behaviour. This makes it useful as a **controlled experiment**: sweep the mix ratio and watch the texture metrics change.

### 2.10 Eller's
Handles one row at a time, assigning each cell to a set. Randomly merge adjacent cells
of different sets in the row. Then each set must carve at least one passage down.
The last row merges all remaining sets. [E], [TL], [MfP ch. 12]
- Memory O(width). It can stream mazes of unbounded height.
- Needs ordered rows with a well-defined "next row". Square fits. Polar fits if outward ring subdivision is handled. Hex needs care with offset rows (Phase 3).

### 2.11 Recursive Division
The only **wall-adding** algorithm here. Start from an open field, add a wall
with a single gap that splits it in two, and recurse into both halves. [MfP ch. 12], [TL]
- Texture: long straight walls, rooms. With a "room size" threshold it can leave open areas (non-perfect).
- Needs rectangular sub-regions, so square only.

### 2.12 Cellular automata (placeholder)
Run a life-like rule (e.g. *Maze* B3/S12345, *Mazectric* B3/S1234) on a random
seed grid. The result is cave/maze-like but **not a perfect maze**: there may be loops,
and cells may be unreachable. Useful as a contrast case for solvers. [TL]

### 2.13 Braiding (post-process placeholder)
Remove some fraction *p* of dead ends by linking each one to a neighbor. This creates loops
("braid" mazes). This is where wall followers and DFS break down and BFS/A* stand
out, so it is an important benchmark axis. [MfP ch. 9]

---

## 3. What this means for the benchmark

1. **Texture is part of the result.** Report dead-end %, corridor length and
   diameter per generator, because these explain solver results. For example,
   DFS mazes have long solution paths, so BFS explores a lot of the maze before
   reaching the goal.
2. **Use uniform generators as the baseline.** Wilson's on topology X is the
   "unbiased" reference maze for X.
3. **Use the Growing Tree mix sweep** as the controlled-variable experiment.
4. **Perfect vs braided** should be a matrix dimension (`braid: [0.0, 0.5, 1.0]`).
