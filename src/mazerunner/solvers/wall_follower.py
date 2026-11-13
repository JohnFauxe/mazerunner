"""Wall follower (left/right hand). param hand='left'|'right' (default 'right').

Reference: Pullen, Think Labyrinth. exits() come in counter-clockwise screen order, so
"the passage immediately after the one I arrived by" is the first turn to the right
(facing away from the arrival passage: back -> right -> straight -> left), and the passage
immediately before it is the first turn to the left. Right hand takes index i+1, left hand
i-1 (mod len) relative to the arrival passage i; a dead end therefore turns around.
At the start there is no arrival passage; we pretend we came in through exits[0].
Works on perfect mazes; on mazes with a loop around the goal it circles forever. The agent
stops (=> FAILED) when it repeats a (cell, arrival passage) state, which is deterministic
looping; otherwise the step budget ends it (TIMEOUT).
"""
from __future__ import annotations

import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401


@solvers.register(
    "wall-follower", title="Wall follower (left/right hand)", requires=(Trait.PLANAR,), phase=Phase.MVP,
    tags=('agent',), implemented=True, reference="Pullen, Think Labyrinth",
)
class WallFollower(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        hand = self.params.get("hand", "right")
        if hand not in ("left", "right"):
            raise ValueError("hand must be 'left' or 'right'")
        delta = 1 if hand == "right" else -1
        seen: set[tuple] = set()
        while not probe.at_goal():
            exits = probe.exits()
            if not exits:
                return
            prev = probe.trail[-2] if len(probe.trail) > 1 else exits[0]
            i = exits.index(prev)
            state = (probe.here, prev)
            if state in seen:
                return
            seen.add(state)
            probe.move(exits[(i + delta) % len(exits)])
