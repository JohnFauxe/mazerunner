"""Random mouse. Random exit, avoid immediate reversal unless dead end.

Reference: Pullen, Think Labyrinth. Terminates only via the step budget (TIMEOUT) if unlucky.
"""
from __future__ import annotations

import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "random-mouse", title="Random mouse", requires=(), phase=Phase.MVP,
    tags=('agent',), implemented=True, reference="Pullen, Think Labyrinth",
)
class RandomMouse(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        while not probe.at_goal():
            exits = probe.exits()
            if not exits:
                return
            prev = probe.trail[-2] if len(probe.trail) > 1 else None
            options = [e for e in exits if e != prev] or exits
            probe.move(rng.choice(options))
