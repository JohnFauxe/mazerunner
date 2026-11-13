"""Cellular automaton (Maze B3/S12345). Life-like rule over random seed. produces_perfect = False.

Reference: Pullen, Think Labyrinth. Notes: docs/algorithms/generation.md
Status: placeholder (phase PLACEHOLDER).
"""
import random

from mazerunner.core.maze import Maze
from mazerunner.core.registry import Phase, generators
from mazerunner.core.traits import Trait  # noqa: F401
from mazerunner.generators.base import Generator


@generators.register(
    "cellular-automaton", title="Cellular automaton (Maze B3/S12345)", requires=(Trait.ORTHOGONAL,), phase=Phase.PLACEHOLDER,
    tags=('non-perfect',), reference="Pullen, Think Labyrinth",
)
class CellularAutomaton(Generator):
    produces_perfect = False

    def carve(self, maze: Maze, rng: random.Random) -> None:
        raise NotImplementedError("cellular-automaton: phase PLACEHOLDER")
