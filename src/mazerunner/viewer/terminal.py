"""Terminal live view for square mazes: redraws the ASCII maze in place as
events arrive (curses-free; ANSI cursor moves). A cheap preview before the web
viewer exists. Phase 1 (after render/ascii.py)."""


def play(trace_path, *, fps: float = 30.0) -> None:
    raise NotImplementedError("terminal viewer: phase 1")
