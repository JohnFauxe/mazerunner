"""Empirical uniformity test (PLAN §3.1).

Enumerate every spanning tree of a tiny topology (e.g. 3×3 square = 192
trees), sample a generator many times, and run a chi-squared goodness-of-fit
test. Aldous–Broder and Wilson's should pass; others quantify their bias.
Phase 3.
"""


def spanning_trees(topology):
    raise NotImplementedError


def chi_squared(generator_key: str, topology, samples: int = 10_000) -> dict:
    raise NotImplementedError
