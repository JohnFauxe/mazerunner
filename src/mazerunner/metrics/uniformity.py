"""Empirical uniformity test (PLAN §3.1).

Enumerate every spanning tree of a tiny topology (3x3 square = 192 trees),
sample a generator many times, and run a chi-squared goodness-of-fit test
against the uniform distribution. Aldous-Broder and Wilson's should pass;
others quantify their bias.
"""

from __future__ import annotations

import math

from mazerunner.core.rng import derive_seed


def _edges(topology) -> list[frozenset]:
    seen: set[frozenset] = set()
    out = []
    for c in topology.cells():
        for n in topology.neighbors(c):
            e = frozenset((c, n))
            if e not in seen:
                seen.add(e)
                out.append(e)
    return out


def spanning_trees(topology) -> list[frozenset]:
    """All spanning trees of the topology graph, each a frozenset of edges
    (edges are frozenset({a, b}), the same form as Maze.links). Backtracking
    over edges with union-find; exponential, for tiny topologies only."""
    cells = topology.cell_list
    idx = {c: i for i, c in enumerate(cells)}
    n = len(cells)
    edges = [tuple(idx[x] for x in e) for e in _edges(topology)]
    raw = _edges(topology)
    m = len(edges)
    results: list[frozenset] = []

    def find(parent, x):
        while parent[x] != x:
            x = parent[x]
        return x

    def connected(parent, start):
        p = parent[:]
        for a, b in edges[start:]:
            ra, rb = find(p, a), find(p, b)
            if ra != rb:
                p[ra] = rb
        root = find(p, 0)
        return all(find(p, i) == root for i in range(n))

    def rec(i, parent, chosen):
        if len(chosen) == n - 1:
            results.append(frozenset(raw[j] for j in chosen))
            return
        if i == m or (n - 1 - len(chosen)) > m - i:
            return
        a, b = edges[i]
        ra, rb = find(parent, a), find(parent, b)
        if ra != rb:  # include
            p2 = parent[:]
            p2[ra] = rb
            rec(i + 1, p2, chosen + [i])
        if connected(parent, i + 1):  # exclude, only if still completable
            rec(i + 1, parent, chosen)

    if n == 0:
        return []
    if n == 1:
        return [frozenset()]
    rec(0, list(range(n)), [])
    return results


def _gammainc_series(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x), series (good for x < a + 1)."""
    ap, term = a, 1.0 / a
    total = term
    for _ in range(10_000):
        ap += 1
        term *= x / ap
        total += term
        if abs(term) < abs(total) * 1e-16:
            break
    return total * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gammainc_cf(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x), Lentz continued fraction (x >= a + 1)."""
    tiny = 1e-300
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-16:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def gammaincc(a: float, x: float) -> float:
    """Regularized upper incomplete gamma function Q(a, x)."""
    if a <= 0:
        raise ValueError("a must be positive")
    if x <= 0:
        return 1.0
    if x < a + 1:
        return 1.0 - _gammainc_series(a, x)
    return _gammainc_cf(a, x)


def chi2_sf(x: float, dof: int) -> float:
    """Chi-squared survival function P(X >= x) with `dof` degrees of freedom."""
    if dof <= 0:
        return 1.0
    return gammaincc(dof / 2, x / 2)


def chi_squared(generator_key: str, topology, samples: int = 10_000, seed: int = 0) -> dict:
    """Generate `samples` mazes (seeds derived from `seed` and the sample index)
    and test the tree frequencies against uniform over all spanning trees.

    Returns {"trees", "samples", "chi2", "dof", "p_value", "unseen"}. A tiny
    p_value rejects uniformity; `unseen` counts trees never produced.
    """
    from mazerunner import api  # lazy: api imports all plugins

    trees = spanning_trees(topology)
    counts = dict.fromkeys(trees, 0)
    for i in range(samples):
        maze = api.generate(topology, generator_key, derive_seed(seed, "uniformity", i))
        t = frozenset(maze.links)
        if t not in counts:
            raise ValueError(f"{generator_key} produced a non-spanning-tree maze")
        counts[t] += 1
    k = len(trees)
    expected = samples / k
    chi2 = sum((o - expected) ** 2 / expected for o in counts.values())
    dof = k - 1
    return {"trees": k, "samples": samples, "chi2": chi2, "dof": dof,
            "p_value": chi2_sf(chi2, dof), "unseen": sum(1 for o in counts.values() if o == 0)}
