"""Trémaux's algorithm. Chalk marks via probe.mark()/marks().

Reference: Lucas 1882. Every passage end is marked when the agent leaves through it and when
it arrives through it, so both ends of a passage always carry the same count (= times walked,
0..2) and the agent can read it from either side. Rules:
  * arriving at a new junction (no other marked exit): take a random unmarked exit;
  * arriving at a known junction by a passage walked for the first time: go back;
  * otherwise take the least-marked exit, never one marked twice.
If every exit is marked twice the maze has no route to the goal and the agent stops (FAILED).
Terminates on any connected maze, including braided ones. The returned path is the walked trail.
"""
from __future__ import annotations

import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "tremaux", title="Trémaux's algorithm", requires=(), phase=Phase.ROUND_HEX,
    tags=('complete', 'agent'), implemented=True, reference="Lucas 1882",
)
class Tremaux(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        def go(to):
            probe.mark(to)  # leaving end
            probe.move(to)
            probe.mark(probe.trail[-2])  # arrival end

        while not probe.at_goal():
            exits = probe.exits()
            if not exits:
                return
            prev = probe.trail[-2] if len(probe.trail) > 1 else None
            others = [e for e in exits if e != prev]
            counts = {e: probe.marks(e) for e in exits}
            if prev is None or all(counts[e] == 0 for e in others):
                # new junction (or start / dead end)
                fresh = [e for e in others if counts[e] == 0]
                if fresh:
                    go(rng.choice(fresh))
                elif prev is not None and counts[prev] < 2:
                    go(prev)
                else:
                    return
            elif counts[prev] == 1:
                go(prev)  # known junction entered by a fresh passage
            else:
                cands = [e for e in exits if counts[e] < 2]
                if not cands:
                    return
                m = min(counts[e] for e in cands)
                go(rng.choice([e for e in cands if counts[e] == m]))
