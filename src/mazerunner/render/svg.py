"""SVG renderer. Each topology supplies cell polygons; walls are drawn for
unlinked neighbor pairs. Polar uses arcs. Phase 2."""

from mazerunner.core.maze import Maze


def render(maze: Maze, path=None, *, cell_size: float = 20.0) -> str:
    raise NotImplementedError("svg render: phase 2")
