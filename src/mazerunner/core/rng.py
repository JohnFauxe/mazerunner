"""Deterministic per-trial seeding (PLAN §4)."""

import hashlib
import random


def derive_seed(*parts: object) -> int:
    h = hashlib.blake2b(repr(parts).encode(), digest_size=8)
    return int.from_bytes(h.digest(), "big")


def rng_for(*parts: object) -> random.Random:
    return random.Random(derive_seed(*parts))
