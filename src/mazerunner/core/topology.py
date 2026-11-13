"""Topology: the cells of a maze and which pairs *could* be linked."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterator, Sequence
from typing import ClassVar

from mazerunner.core.traits import Trait

Cell = Hashable


class Topology(ABC):
    """Immutable cell graph. One instance is shared across many mazes or trials."""

    name: ClassVar[str]
    traits: ClassVar[frozenset[Trait]] = frozenset()

    # --- required by every topology -------------------------------------
    @abstractmethod
    def cells(self) -> Iterator[Cell]:
        """All cells, in a deterministic order (Hunt-and-Kill relies on this)."""

    @abstractmethod
    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        """Adjacent cells. If PLANAR, in counter-clockwise cyclic order."""

    @abstractmethod
    def __len__(self) -> int: ...

    def has(self, trait: Trait) -> bool:
        return trait in self.traits

    # --- trait-specific hooks (override when the trait is declared) -----
    def rows(self) -> Sequence[Sequence[Cell]]:
        """ROWS: cells grouped into ordered rows or rings."""
        raise NotImplementedError(f"{self.name} lacks Trait.ROWS")

    def heading(self, src: Cell, dst: Cell) -> float:
        """HEADINGS: absolute direction of travel src→dst, in radians."""
        raise NotImplementedError(f"{self.name} lacks Trait.HEADINGS")

    def distance(self, a: Cell, b: Cell) -> float:
        """METRIC: admissible lower bound on path length a→b."""
        raise NotImplementedError(f"{self.name} lacks Trait.METRIC")

    def position(self, cell: Cell) -> tuple[float, float]:
        """Layout coordinates for rendering (centre of cell)."""
        raise NotImplementedError

    def boundary(self) -> list[Cell]:
        """Boundary cells in cyclic order, starting mid-way along the first side.
        Used by the default 'opposite-sides' endpoint placement."""
        raise NotImplementedError(f"{self.name}.boundary()")

    def geometry(self) -> dict:
        """Drawable shapes for the viewer/SVG: {cells: [polygon | arc spec], walls: {...}}.
        Written into trace headers so the web viewer stays topology-agnostic."""
        raise NotImplementedError(f"{self.name}.geometry()")

    def default_endpoints(self) -> tuple[Cell, Cell]:
        """Fallback start/goal when the config doesn't specify them."""
        cs = list(self.cells())
        return cs[0], cs[-1]
