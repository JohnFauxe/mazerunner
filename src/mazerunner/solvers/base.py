"""Solver interfaces: omniscient (sees whole maze) vs agent (sandboxed Probe)."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from mazerunner.core.maze import Maze
from mazerunner.core.topology import Cell
from mazerunner.core.trace import NULL, Tracer


class Outcome(str, Enum):
    SOLVED = "solved"
    FAILED = "failed"      # terminated without reaching goal (e.g. wall follower island)
    TIMEOUT = "timeout"    # exceeded step budget


@dataclass
class SolveResult:
    outcome: Outcome
    path: list[Cell] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)  # nodes_expanded, steps, probes…


class Solver(ABC):
    key: ClassVar[str]
    mode: ClassVar[str]

    def __init__(self, **params) -> None:
        self.params = params
        self.tracer: Tracer = NULL  # set by runner/viewer; emit visit/frontier_add/…


class OmniscientSolver(Solver):
    mode = "omniscient"

    @abstractmethod
    def solve(self, maze: Maze, rng: random.Random) -> SolveResult: ...


class Probe:
    """The only view an agent solver gets of the maze. Every call is counted."""

    def __init__(self, maze: Maze, step_budget: int | None = None, tracer: Tracer = NULL) -> None:
        self._maze = maze
        self._tracer = tracer
        self.here: Cell = maze.start
        self.trail: list[Cell] = [self.here]
        self.budget = step_budget if step_budget is not None else 10 * len(maze.topology)
        self._marks: dict[tuple[Cell, Cell], int] = {}
        self.counters = {"steps": 0, "probes": 0, "revisits": 0}
        self._seen = {self.here}

    def exits(self) -> list[Cell]:
        """Open passages from `here`, in cyclic order if the topology is PLANAR."""
        self.counters["probes"] += 1
        return self._maze.passages(self.here)

    def move(self, cell: Cell) -> None:
        if not self._maze.linked(self.here, cell):
            raise ValueError("agent tried to walk through a wall")
        if self.counters["steps"] >= self.budget:
            raise TimeoutError
        self.counters["steps"] += 1
        if cell in self._seen:
            self.counters["revisits"] += 1
        self._seen.add(cell)
        self.here = cell
        self.trail.append(cell)
        self._tracer.emit("move", cell)

    def at_goal(self) -> bool:
        return self.here == self._maze.goal

    # Trémaux chalk marks on passage entrances
    def mark(self, toward: Cell) -> None:
        k = (self.here, toward)
        self._marks[k] = self._marks.get(k, 0) + 1
        self._tracer.emit("mark", self.here, toward, count=self._marks[k])

    def marks(self, toward: Cell) -> int:
        return self._marks.get((self.here, toward), 0)

    # HEADINGS: exposed for Pledge (needs to know absolute direction)
    def heading(self, toward: Cell) -> float:
        return self._maze.topology.heading(self.here, toward)


class AgentSolver(Solver):
    mode = "agent"

    @abstractmethod
    def run(self, probe: Probe, rng: random.Random) -> None:
        """Walk until probe.at_goal() or give up (return). Raise nothing on failure."""

    def solve(self, maze: Maze, rng: random.Random) -> SolveResult:
        probe = Probe(maze, self.params.get("step_budget"), self.tracer)
        try:
            self.run(probe, rng)
            outcome = Outcome.SOLVED if probe.at_goal() else Outcome.FAILED
        except TimeoutError:
            outcome = Outcome.TIMEOUT
        return SolveResult(outcome, probe.trail, dict(probe.counters))
