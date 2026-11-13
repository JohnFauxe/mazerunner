"""Pledge algorithm. Preferred heading + wall following with a signed turn counter.

Reference: Abelson & diSessa 1980. Agents do not know where the goal is, so this is the
escape formulation: walk in the preferred absolute heading (param `heading`, radians, default
0 = east; param `hand`='left'|'right', default 'left') until blocked, then follow the wall
while summing the signed heading changes (CCW positive, each normalised to (-pi, pi]; a U-turn
counts +pi for the right hand and -pi for the left hand). When the sum is back to 0 and the
preferred direction is open, leave the wall. Pledge escapes to the outside of a maze; it may
never reach an interior goal, and then ends via the step budget (TIMEOUT), or FAILED if it
repeats an exact state. Stops successfully when probe.at_goal().
"""
from __future__ import annotations

import math
import random

from mazerunner.core.maze import Maze  # noqa: F401
from mazerunner.core.registry import Phase, solvers
from mazerunner.core.traits import Trait
from mazerunner.solvers.base import AgentSolver, Probe, SolveResult  # noqa: F401

_TAU = 2 * math.pi
_EPS = 1e-6


def _norm(a: float) -> float:
    """Normalise an angle to (-pi, pi]."""
    a = math.fmod(a, _TAU)
    if a <= -math.pi:
        a += _TAU
    elif a > math.pi:
        a -= _TAU
    return a


@solvers.register(
    "pledge", title="Pledge algorithm", requires=(Trait.PLANAR, Trait.HEADINGS), phase=Phase.ANALYSIS,
    tags=('escape', 'agent'), implemented=True, reference="Abelson & diSessa 1980",
)
class Pledge(AgentSolver):
    def run(self, probe: Probe, rng: random.Random) -> None:
        hand = self.params.get("hand", "left")
        if hand not in ("left", "right"):
            raise ValueError("hand must be 'left' or 'right'")
        pref = float(self.params.get("heading", 0.0))
        tol = math.pi / 4 - 1e-9
        u_turn = -math.pi if hand == "left" else math.pi
        facing, total, wall_mode = pref, 0.0, False
        seen: set[tuple] = set()
        while not probe.at_goal():
            exits = probe.exits()
            if not exits:
                return
            hs = {e: probe.heading(e) for e in exits}
            straight = min(exits, key=lambda e: abs(_norm(hs[e] - pref)))
            straight_open = abs(_norm(hs[straight] - pref)) < tol
            if wall_mode and abs(total) < _EPS and straight_open:
                wall_mode = False
            state = (probe.here, wall_mode, round(facing, 5), round(total, 5))
            if state in seen:
                return
            seen.add(state)
            if not wall_mode:
                if straight_open:
                    nxt = straight
                else:
                    wall_mode = True
            if wall_mode:
                def key(e):
                    d = _norm(hs[e] - facing)
                    if abs(abs(d) - math.pi) < _EPS:
                        return (1, 0.0)  # reversing is the last resort
                    return (0, -d if hand == "left" else d)
                nxt = min(exits, key=key)
            d = _norm(hs[nxt] - facing)
            if abs(abs(d) - math.pi) < _EPS:
                d = u_turn
            facing = hs[nxt]
            if wall_mode:
                total += d
            probe.move(nxt)
