"""Maze <-> JSON: {"version", "topology", "links", "start", "goal", "meta"}."""

from __future__ import annotations

import json
from pathlib import Path

from mazerunner.core.maze import Maze

VERSION = 1


def _cell_args(args):
    return [tuple(a) if isinstance(a, list) else a for a in args]


def to_dict(maze: Maze) -> dict:
    topo = maze.topology
    idx = topo.index
    links = sorted(sorted((idx[a], idx[b])) for a, b in (tuple(e) for e in maze.links))
    return {
        "version": VERSION,
        "topology": topo.describe(),
        "links": links,
        "start": None if maze.start is None else idx[maze.start],
        "goal": None if maze.goal is None else idx[maze.goal],
        "meta": maze.meta,
    }


def dumps(maze: Maze, *, indent: int | None = None) -> str:
    return json.dumps(to_dict(maze), indent=indent, default=str)


def from_dict(d: dict) -> Maze:
    from mazerunner.core import registry
    try:
        registry.load_all()
    except Exception:  # another plugin module is broken; topologies are enough
        import mazerunner.topologies  # noqa: F401
    if d.get("version", VERSION) != VERSION:
        raise ValueError(f"unsupported maze version {d.get('version')!r}")
    desc = d["topology"]
    topo = registry.topologies.get(desc["name"]).obj(*_cell_args(desc.get("args", [])))
    cl = topo.cell_list
    maze = Maze(topo, start=None if d.get("start") is None else cl[d["start"]],
                goal=None if d.get("goal") is None else cl[d["goal"]],
                meta=dict(d.get("meta") or {}))
    for i, j in d["links"]:
        maze.link(cl[i], cl[j])
    return maze


def loads(s: str) -> Maze:
    return from_dict(json.loads(s))


def save(maze: Maze, path, *, indent: int | None = None) -> None:
    Path(path).write_text(dumps(maze, indent=indent), encoding="utf-8")


def load(path) -> Maze:
    return loads(Path(path).read_text(encoding="utf-8"))
