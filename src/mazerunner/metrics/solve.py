"""Solver outcome metrics (PLAN §3.3)."""

from __future__ import annotations

from mazerunner.core.maze import Maze


def solve_metrics(maze: Maze, result) -> dict:
    """Quality of one SolveResult against BFS ground truth.

    path_len = cells in result.path (agent trails may revisit cells); steps =
    path_len - 1; optimal_len = shortest path in steps (None if unreachable);
    optimality = optimal_len / steps for solved runs (1.0 = optimal; None
    otherwise); valid = path starts at start, ends at goal and every consecutive
    pair is linked (revisits allowed). A solved outcome with an invalid path
    gets valid=False.
    """
    outcome = getattr(result.outcome, "value", result.outcome)
    path = list(result.path)
    steps = max(0, len(path) - 1)
    optimal = maze.shortest_path_length()
    optimality = None
    if outcome == "solved" and optimal is not None:
        optimality = 1.0 if steps == 0 else optimal / steps
    return {
        "outcome": outcome,
        "path_len": len(path),
        "steps": steps,
        "optimal_len": optimal,
        "optimality": optimality,
        "valid": bool(path) and maze.verify_path(path),
        "counters": dict(result.counters),
    }
