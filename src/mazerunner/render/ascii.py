"""ASCII / unicode box renderer for square (ORTHOGONAL + ROWS) mazes."""

from __future__ import annotations

from collections.abc import Callable

from mazerunner.core.maze import Maze
from mazerunner.core.traits import Trait

# unicode box glyphs indexed by (up, right, down, left) wall presence
_BOX = {
    (0, 0, 0, 0): " ", (1, 0, 1, 0): "│", (0, 1, 0, 1): "─",
    (0, 1, 1, 0): "┌", (0, 0, 1, 1): "┐", (1, 1, 0, 0): "└", (1, 0, 0, 1): "┘",
    (1, 1, 1, 0): "├", (1, 0, 1, 1): "┤", (0, 1, 1, 1): "┬", (1, 1, 0, 1): "┴",
    (1, 1, 1, 1): "┼",
    (1, 0, 0, 0): "╵", (0, 1, 0, 0): "╶", (0, 0, 1, 0): "╷", (0, 0, 0, 1): "╴",
}


def draw_grid(rows: int, cols: int, linked: Callable[[int, int, str], bool],
              cell_text: Callable[[int, int], str], style: str = "box") -> str:
    """Draw a rows x cols grid. `linked(r, c, "E"|"S")` says whether the cell is
    open towards its east/south neighbour; `cell_text(r, c)` is the 3-char
    interior (may contain ANSI codes)."""
    if style not in ("box", "unicode"):
        raise ValueError(f"unknown style {style!r}")
    # wall presence on the lattice: H[i][c] wall above/below cell column c on
    # lattice row i (0..rows); V[r][j] wall left/right of row r on lattice col j.
    H = [[True] * cols for _ in range(rows + 1)]
    V = [[True] * (cols + 1) for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols and linked(r, c, "E"):
                V[r][c + 1] = False
            if r + 1 < rows and linked(r, c, "S"):
                H[r + 1][c] = False
    uni = style == "unicode"
    hw, vw = ("───", "│") if uni else ("---", "|")
    out = []
    for i in range(rows + 1):
        line = []
        for j in range(cols + 1):
            if uni:
                up = i > 0 and V[i - 1][j]
                down = i < rows and V[i][j]
                left = j > 0 and H[i][j - 1]
                right = j < cols and H[i][j]
                line.append(_BOX[(int(up), int(right), int(down), int(left))])
            else:
                line.append("+")
            if j < cols:
                line.append(hw if H[i][j] else "   ")
        out.append("".join(line))
        if i == rows:
            break
        line = []
        for j in range(cols + 1):
            line.append(vw if V[i][j] else " ")
            if j < cols:
                line.append(cell_text(i, j))
        out.append("".join(line))
    return "\n".join(out)


def render(maze: Maze, path=None, *, marks: dict | None = None, style: str = "box",
           path_char: str = "·") -> str:
    topo = maze.topology
    if not (topo.has(Trait.ORTHOGONAL) and topo.has(Trait.ROWS)):
        raise ValueError(f"ascii render needs an orthogonal row topology, not {topo.name!r}")
    rows = topo.rows()
    R, C = len(rows), len(rows[0])
    on_path = set(path or ())
    marks = marks or {}

    def linked(r, c, d):
        cell = rows[r][c]
        n = topo.axis_neighbor(cell, d)
        return n is not None and maze.linked(cell, n)

    def text(r, c):
        cell = rows[r][c]
        if cell == maze.start:
            return " S "
        if cell == maze.goal:
            return " G "
        if cell in marks:
            return f" {str(marks[cell])[:1] or ' '} "
        if cell in on_path:
            return f" {path_char} "
        return "   "

    return draw_grid(R, C, linked, text, style)
