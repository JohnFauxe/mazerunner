"""Local viewer server. Stdlib only (http.server + Server-Sent Events).

Routes (planned)
  GET /                      static viewer app (static/index.html)
  GET /api/traces            list recorded *.trace.jsonl files
  GET /api/traces/<name>     one trace (header + events) for replay
  GET /api/live?cfg=...      SSE stream: runs generator/solver now with a
                             StreamTracer and pushes events as they happen
  GET /api/results           benchmark results (results/*.jsonl) for the dashboard

Phase 2 (replay + live), phase 3 (results dashboard).
"""

from pathlib import Path

STATIC = Path(__file__).parent / "static"


def serve(host: str = "127.0.0.1", port: int = 8765, traces_dir: Path = Path("traces"),
          results_dir: Path = Path("results")) -> None:
    raise NotImplementedError("viewer server: phase 2")
