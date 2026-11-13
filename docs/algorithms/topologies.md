# Topologies — Research Notes

> **TL;DR** — Each topology is a cell graph plus traits. Square is the
> reference. Polar (round) subdivides outer rings to keep cell width roughly
> constant. Hex uses axial coordinates. Triangle, upsilon, weave, 3D and masked
> shapes are planned as drop-in modules.

Reference: [MfP] Buck, *Mazes for Programmers*: ch. 7 (polar), ch. 8 (hex, triangle), ch. 9 (weave), ch. 13 (3D, cylinder, Möbius, sphere). [TL] Pullen's dimension/tessellation taxonomy.

| Topology | Cell id | Degree | Traits | Phase |
|---|---|---|---|---|
| Square | `(row, col)` | ≤4 | ROWS, ORTHOGONAL, RECTANGULAR, PLANAR, HEADINGS, METRIC, UNIFORM_GRID | 1 |
| Polar | `(ring, index)` | 3–5 (inward 1, outward 1–2, cw/ccw) | ROWS, PLANAR, HEADINGS, METRIC | 2 |
| Hex | `(q, r)` axial | ≤6 | ROWS, PLANAR, HEADINGS, METRIC | 2 |
| Triangle | `(row, col)` + up/down parity | ≤3 | ROWS, PLANAR, HEADINGS, METRIC | placeholder |
| Upsilon | `(row, col)` alternating octagon/square | 4 or 8 | ROWS, PLANAR, METRIC | placeholder |
| Weave | square + crossing cells | ≤4 (+ under-passes) | as square + WEAVE (not PLANAR) | placeholder |
| 3D / multi-level | `(level, row, col)` | ≤6 | ROWS, METRIC | placeholder |
| Masked / arbitrary | any | any | none guaranteed | placeholder |

## Polar construction (Buck ch. 7)
Ring 0 is a single centre cell. Ring *r* has `cells(r-1) * k` cells, where
`k = round((2πr / cells(r-1)) / ring_height)`, so cells stay roughly square. Each
cell links inward to one parent and outward to 1 or more children.

## Hex
Use axial `(q, r)` with neighbor offsets `(+1,0) (+1,-1) (0,-1) (-1,0) (-1,+1) (0,+1)`
in cyclic order, which gives PLANAR for free. Lay out as a parallelogram or a "rectangular" offset
board (Buck uses offset columns), configurable.
