"""Topology: the cells of a maze and which pairs *could* be linked.

Contract summary (every topology MUST implement the first block; trait hooks
only when the trait is declared):

    cells(), neighbors(cell), __len__()               always
    boundary(), position(cell), geometry()            always (viewer/endpoints)
    rows(), row_of(), next_in_row(),
      prev_row_neighbors(), next_row_neighbors()      Trait.ROWS
    axis_neighbor(cell, "N"|"S"|"E"|"W")              Trait.ORTHOGONAL
    heading(src, dst)                                 Trait.HEADINGS
    distance(a, b)                                    Trait.METRIC

Geometry contract (consumed by the SVG renderer and the web viewer, which know
nothing about specific topologies)::

    {
      "width": float, "height": float,          # drawing bounds, origin top-left, y down
      "cells": [[[x, y], ...], ...],             # polygon per cell, indexed by index()[cell]
      "walls": [{"a": i, "b": j | None,          # wall between cells i and j; b=None = outer wall
                 "pts": [[x, y], ...]}, ...]     # polyline (arcs are approximated)
    }

A wall is drawn when b is None or cells a and b are NOT linked.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable, Iterator, Sequence
from functools import cached_property
from typing import ClassVar

from mazerunner.core.traits import Trait

Cell = Hashable


class Topology(ABC):
    """Immutable cell graph. One instance is shared across many mazes/trials."""

    name: ClassVar[str]
    traits: ClassVar[frozenset[Trait]] = frozenset()

    # --- required by every topology -------------------------------------
    @abstractmethod
    def cells(self) -> Iterator[Cell]:
        """All cells, in a deterministic order (Hunt-and-Kill relies on this)."""

    @abstractmethod
    def neighbors(self, cell: Cell) -> Sequence[Cell]:
        """Adjacent cells. If PLANAR: counter-clockwise *as drawn on screen*."""

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def boundary(self) -> list[Cell]:
        """Boundary cells in cyclic order (a cell may repeat, e.g. square corners
        once per side), starting at the middle of the *west/left* side.
        `boundary()[i]` and `boundary()[i + n//2]` are on opposite sides."""

    @abstractmethod
    def position(self, cell: Cell) -> tuple[float, float]:
        """Centre of the cell in geometry() coordinates."""

    @abstractmethod
    def geometry(self) -> dict:
        """Drawable shapes; see module docstring."""

    # --- helpers --------------------------------------------------------
    def has(self, trait: Trait) -> bool:
        return trait in self.traits

    @cached_property
    def index(self) -> dict[Cell, int]:
        """cell -> stable integer id (order of cells())."""
        return {c: i for i, c in enumerate(self.cells())}

    @cached_property
    def cell_list(self) -> list[Cell]:
        return list(self.cells())

    def center(self) -> Cell:
        """Cell nearest the drawing centre (used by 'center-out' placement)."""
        g = self.geometry()
        cx, cy = g["width"] / 2, g["height"] / 2
        return min(self.cells(), key=lambda c: (self.position(c)[0] - cx) ** 2
                   + (self.position(c)[1] - cy) ** 2)

    def default_endpoints(self) -> tuple[Cell, Cell]:
        cs = self.cell_list
        return cs[0], cs[-1]

    def describe(self) -> dict:
        """Constructor info for serialisation: {"name": ..., "args": [...]}."""
        return {"name": self.name, "args": list(getattr(self, "args", ()))}

    # --- Trait.ROWS -----------------------------------------------------
    def rows(self) -> Sequence[Sequence[Cell]]:
        """Cells grouped in ordered rows (square: top→bottom; polar: rings inner→outer)."""
        raise NotImplementedError(f"{self.name} lacks Trait.ROWS")

    def row_of(self, cell: Cell) -> int:
        raise NotImplementedError(f"{self.name} lacks Trait.ROWS")

    def next_in_row(self, cell: Cell) -> Cell | None:
        """Following cell in the same row ("east"), None at the row end (no wrap)."""
        raise NotImplementedError(f"{self.name} lacks Trait.ROWS")

    def prev_row_neighbors(self, cell: Cell) -> list[Cell]:
        """Adjacent cells in row_of(cell) - 1 ("north"/inward)."""
        raise NotImplementedError(f"{self.name} lacks Trait.ROWS")

    def next_row_neighbors(self, cell: Cell) -> list[Cell]:
        """Adjacent cells in row_of(cell) + 1 ("south"/outward)."""
        raise NotImplementedError(f"{self.name} lacks Trait.ROWS")

    # --- Trait.ORTHOGONAL -----------------------------------------------
    def axis_neighbor(self, cell: Cell, direction: str) -> Cell | None:
        """direction in {"N", "S", "E", "W"}; None off the edge."""
        raise NotImplementedError(f"{self.name} lacks Trait.ORTHOGONAL")

    # --- Trait.HEADINGS -------------------------------------------------
    def heading(self, src: Cell, dst: Cell) -> float:
        """Absolute direction src→dst in radians, maths convention (E=0, N=π/2)."""
        raise NotImplementedError(f"{self.name} lacks Trait.HEADINGS")

    # --- Trait.METRIC ---------------------------------------------------
    def distance(self, a: Cell, b: Cell) -> float:
        """Admissible lower bound on the number of steps a→b."""
        raise NotImplementedError(f"{self.name} lacks Trait.METRIC")
