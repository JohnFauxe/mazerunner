"""Plugin registries. Each algorithm/topology module registers itself on import."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mazerunner.core.traits import Trait


class Phase(str, Enum):
    MVP = "1"
    ROUND_HEX = "2"
    ANALYSIS = "3"
    PLACEHOLDER = "4"


@dataclass(frozen=True)
class AlgorithmInfo:
    key: str
    title: str
    obj: Any
    requires: frozenset[Trait] = frozenset()
    phase: Phase = Phase.PLACEHOLDER
    implemented: bool = False
    tags: frozenset[str] = field(default_factory=frozenset)  # e.g. {"uniform"}, {"agent"}
    reference: str = ""

    def compatible(self, traits: frozenset[Trait]) -> tuple[bool, frozenset[Trait]]:
        missing = self.requires - traits
        return (not missing, missing)


class Registry:
    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._items: dict[str, AlgorithmInfo] = {}

    def register(self, key: str, *, title: str, requires=(), phase=Phase.PLACEHOLDER,
                 implemented: bool = False, tags=(), reference: str = "") -> Callable:
        def deco(obj):
            if key in self._items:
                raise ValueError(f"duplicate {self.kind} {key!r}")
            self._items[key] = AlgorithmInfo(
                key, title, obj, frozenset(requires), phase, implemented,
                frozenset(tags), reference,
            )
            obj.key = key
            return obj
        return deco

    def get(self, key: str) -> AlgorithmInfo:
        return self._items[key]

    def all(self) -> list[AlgorithmInfo]:
        return sorted(self._items.values(), key=lambda i: (i.phase.value, i.key))

    def __contains__(self, key: str) -> bool:
        return key in self._items


generators = Registry("generator")
solvers = Registry("solver")
topologies = Registry("topology")


def load_all() -> None:
    """Import every plugin module so the registries are populated."""
    import mazerunner.generators  # noqa: F401
    import mazerunner.solvers  # noqa: F401
    import mazerunner.topologies  # noqa: F401
