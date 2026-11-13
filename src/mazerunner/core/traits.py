"""Topology capability traits. See PLAN.md §2.2."""

from enum import Enum, auto


class Trait(Enum):
    ROWS = auto()          # cells arranged in ordered rows / rings
    ORTHOGONAL = auto()    # distinct "north" and "east" style axes
    RECTANGULAR = auto()   # region can be split by straight walls
    PLANAR = auto()        # consistent cyclic neighbor ordering in the plane
    HEADINGS = auto()      # absolute headings exist (turn counting)
    METRIC = auto()        # coordinates + admissible distance heuristic
    UNIFORM_GRID = auto()  # square lattice, uniform cost
    WEAVE = auto()         # passages may cross over/under
