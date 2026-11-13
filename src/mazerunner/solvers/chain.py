"""Chain algorithm (simplified). Follow the straight line to the goal, wall-following around obstacles.

Reference: Pullen, Think Labyrinth. Simplification: Pullen's chain walks along a drawn line to
the goal; here the agent is given a distance-to-goal function (topology.distance, so METRIC is
required; the Probe itself does not expose it) and walks greedily: take the exit that most
reduces the distance. When no exit is closer it records d0 = distance there and follows the
right-hand wall until it stands on a cell strictly closer than d0, then resumes the greedy walk.
d0 strictly decreases, so on a perfect maze (where the wall walk visits every cell, including
the goal) it always finishes; on braided mazes it may loop and ends via the step budget or by
repeating a state (FAILED).
"""
from __future__ import annotations

import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult


@solvers.register(
    "chain", title="Chain algorithm", requires=(Trait.METRIC,), phase=Phase.PLACEHOLDER,
    tags=('agent',), implemented=True, reference="Pullen, Think Labyrinth",
)
class Chain(AgentSolver):
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        goal, topo = maze.goal, maze.topology
        self._dist = lambda c: topo.distance(c, goal)
        return super().solve(maze, rng)

    def run(self, probe: Probe, rng: random.Random) -> None:
        dist = self._dist
        d0: float | None = None  # distance where wall following began; None = greedy mode
        seen: set[tuple] = set()
        while not probe.at_goal():
            exits = probe.exits()
            if not exits:
                return
            here = dist(probe.here)
            if d0 is not None and here < d0:
                d0 = None
            if d0 is None:
                best = min(exits, key=dist)
                if dist(best) < here:
                    probe.move(best)
                    continue
                d0 = here
            prev = probe.trail[-2] if len(probe.trail) > 1 else exits[0]
            state = (probe.here, prev, d0)
            if state in seen:
                return
            seen.add(state)
            probe.move(exits[(exits.index(prev) + 1) % len(exits)])  # right-hand rule
