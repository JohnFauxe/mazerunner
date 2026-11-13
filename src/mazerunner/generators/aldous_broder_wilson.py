"""Aldous–Broder → Wilson hybrid. A–B until a fraction of cells visited, then Wilson's.

Reference: Buck, MfP ch.4 notes. Notes: docs/algorithms/generation.md
Status: placeholder (phase PLACEHOLDER).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "ab-wilson-hybrid", title="Aldous–Broder → Wilson hybrid", requires=(), phase=Phase.PLACEHOLDER,
    tags=('uniform',), reference="Buck, MfP ch.4 notes",
)
class AldousBroderWilson(Generator):

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("ab-wilson-hybrid: phase PLACEHOLDER")
