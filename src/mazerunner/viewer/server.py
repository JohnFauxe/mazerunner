"""Local viewer server. Stdlib only (http.server + Server-Sent Events).

    from mazerunner.viewer.server import serve, make_server
    serve(port=8765)                      # blocking
    srv = make_server(port=0); srv.serve_forever()   # embedding / tests

Routes
  GET  /                      static viewer app (static/index.html)
  GET  /api/catalog           topologies / generators / solvers / placements
  GET  /api/traces            recorded *.trace.jsonl files (+ header summary)
  GET  /api/traces/<name>     {"header", "events", "footer"}
  POST /api/run               one maze, N solvers, all recorded in memory
  GET  /api/live?...          SSE stream (header, gen, solve-start, solve, solve-end, done)
  GET  /api/results           results/*.jsonl files
  GET  /api/results/<name>    {"rows": [...]}
"""

from __future__ import annotations

import json
import mimetypes
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from mazerunner import api
from mazerunner.core.endpoints import Placement
from mazerunner.core.registry import generators, solvers, topologies
from mazerunner.core.trace import Recorder, StreamTracer, read_trace

STATIC = Path(__file__).parent / "static"
MAX_CELLS = 40_000
DEFAULT_SIZES = {"square": [20, 20], "polar": [10], "hex": [15, 15]}
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]*$")

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")


class BadRequest(Exception):
    pass


class ClientGone(Exception):
    pass


def _catalog() -> dict:
    def algo(i):
        return {"key": i.key, "title": i.title, "implemented": i.implemented,
                "requires": sorted(t.name for t in i.requires), "tags": sorted(i.tags),
                "phase": i.phase.value}

    tops = []
    for i in topologies.all():
        traits = getattr(i.obj, "traits", frozenset())
        tops.append({"key": i.key, "title": i.title, "implemented": i.implemented,
                     "traits": sorted(t.name for t in traits),
                     "default_size": DEFAULT_SIZES.get(i.key, [8, 8])})
    return {"topologies": tops, "generators": [algo(i) for i in generators.all()],
            "solvers": [algo(i) for i in solvers.all()],
            "placements": [p.value for p in Placement]}


def _parse_cfg(c: dict) -> dict:
    """Normalise + validate a run config (from JSON body or query string)."""
    try:
        topology = c.get("topology") or "square"
        if topology not in topologies:
            raise BadRequest(f"unknown topology {topology!r}")
        size = c.get("size")
        if size is None or size == "":
            size = DEFAULT_SIZES.get(topology, [8, 8])
        if isinstance(size, str):
            size = [int(x) for x in size.replace("x", ",").split(",") if x.strip()]
        size = [int(x) for x in size]
        if not size or any(x < 1 for x in size):
            raise BadRequest("size must be positive integers")
        n = 1
        for x in size:
            n *= x
        if n > MAX_CELLS:
            raise BadRequest(f"maze too large for the viewer ({n} > {MAX_CELLS} cells)")
        gen = c.get("generator")
        if not gen or gen not in generators:
            raise BadRequest(f"unknown generator {gen!r}")
        sl = c.get("solvers") or []
        if isinstance(sl, str):
            sl = [s for s in sl.split(",") if s]
        for s in sl:
            if s not in solvers:
                raise BadRequest(f"unknown solver {s!r}")
        ep = dict(c.get("endpoints") or {})
        ep = {k: v for k, v in ep.items() if v not in (None, "")}
        if "side" in ep:
            ep["side"] = float(ep["side"])
        if "placement" in ep:
            Placement(ep["placement"])
        return {"topology": topology, "size": size, "generator": gen, "solvers": sl,
                "seed": int(c.get("seed") or 0), "endpoints": ep,
                "braid": float(c.get("braid") or 0), "gen_params": c.get("gen_params") or {},
                "solver_params": c.get("solver_params") or {}}
    except BadRequest:
        raise
    except (ValueError, TypeError) as e:
        raise BadRequest(f"bad parameter: {e}") from e


def _topo(cfg):
    try:
        topo = api.make_topology(cfg["topology"], cfg["size"])
        if len(topo) > MAX_CELLS:
            raise BadRequest(f"maze too large for the viewer ({len(topo)} > {MAX_CELLS} cells)")
        return topo
    except NotImplementedError as e:
        raise BadRequest(f"{cfg['topology']}: not implemented ({e})") from e
    except (ValueError, TypeError) as e:
        raise BadRequest(f"cannot build topology: {e}") from e


def _guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except NotImplementedError as e:
        raise BadRequest(f"not implemented: {e or 'algorithm is a placeholder'}") from e
    except (ValueError, KeyError, TypeError) as e:
        raise BadRequest(str(e.args[0] if e.args else e)) from e


def _result(maze, r) -> dict:
    return {"outcome": r.outcome.value, "path_len": len(r.path), "counters": r.counters,
            "optimal": maze.shortest_path_length()}


def _run(cfg: dict) -> dict:
    topo = _topo(cfg)
    base = dict(generator=cfg["generator"], seed=cfg["seed"], braid=cfg["braid"],
                endpoints=cfg["endpoints"])
    rec = Recorder(topo.index, api.trace_header(topo, **base))
    maze = _guard(api.generate, topo, cfg["generator"], cfg["seed"], params=cfg["gen_params"],
                  endpoints=cfg["endpoints"], braid=cfg["braid"], tracer=rec)
    rec.header.update(start=topo.index[maze.start], goal=topo.index[maze.goal],
                      solvers=cfg["solvers"], size=cfg["size"])
    solves = {}
    for key in cfg["solvers"]:
        sr = Recorder(topo.index)
        r = _guard(api.solve, maze, key, cfg["seed"], params=cfg["solver_params"], tracer=sr)
        solves[key] = {"events": sr.events, "result": _result(maze, r)}
    return {"header": rec.header, "generation": rec.events, "solves": solves}


def _summary(header: dict) -> dict:
    t = header.get("topology")
    return {"topology": t.get("name") if isinstance(t, dict) else t,
            "generator": header.get("generator"), "solver": header.get("solver"),
            "seed": header.get("seed")}


def _safe_name(name: str, suffix: str) -> str:
    name = unquote(name)
    if not NAME_RE.match(name) or ".." in name or not name.endswith(suffix):
        raise FileNotFoundError(name)
    return name


class Handler(BaseHTTPRequestHandler):
    server_version = "MazeRunnerViewer/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quiet
        pass

    # ---- helpers -----------------------------------------------------
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, default=str).encode(), "application/json")

    def _error(self, code: int, msg: str):
        self._json({"error": msg}, code)

    # ---- routing -----------------------------------------------------
    def do_GET(self):
        try:
            url = urlparse(self.path)
            path = url.path
            if path.startswith("/api/"):
                self._api_get(path, parse_qs(url.query))
            else:
                self._static(path)
        except (BrokenPipeError, ConnectionResetError, ClientGone):
            self.close_connection = True
        except BadRequest as e:
            self._safe_error(400, str(e))
        except FileNotFoundError:
            self._safe_error(404, "not found")
        except Exception as e:  # noqa: BLE001 - surface to the UI
            self._safe_error(500, f"{type(e).__name__}: {e}")

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            n = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
                if not isinstance(body, dict):
                    raise ValueError
            except ValueError:
                raise BadRequest("body must be a JSON object") from None
            if path != "/api/run":
                raise FileNotFoundError(path)
            self._json(_run(_parse_cfg(body)))
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except BadRequest as e:
            self._safe_error(400, str(e))
        except FileNotFoundError:
            self._safe_error(404, "not found")
        except Exception as e:  # noqa: BLE001
            self._safe_error(500, f"{type(e).__name__}: {e}")

    def _safe_error(self, code, msg):
        try:
            self._error(code, msg)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def _static(self, path: str):
        rel = unquote(path).lstrip("/") or "index.html"
        if "\x00" in rel:
            raise FileNotFoundError(rel)
        root = STATIC.resolve()
        f = (root / rel).resolve()
        if root not in f.parents or not f.is_file():
            raise FileNotFoundError(rel)
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("json"):
            ctype += "; charset=utf-8"
        self._send(200, f.read_bytes(), ctype)

    def _api_get(self, path: str, q: dict):
        srv = self.server
        if path == "/api/catalog":
            return self._json(_catalog())
        if path == "/api/traces":
            seen, out = set(), []
            for d in srv.trace_dirs():
                for item in self._list_traces(d):
                    if item["name"] not in seen:
                        seen.add(item["name"])
                        out.append(item)
            return self._json(out)
        if path.startswith("/api/traces/"):
            name = _safe_name(path[len("/api/traces/"):], ".trace.jsonl")
            f = next((d / name for d in srv.trace_dirs() if (d / name).is_file()), None)
            if f is None:
                raise FileNotFoundError(name)
            with open(f) as fp:
                h, ev, ft = read_trace(fp)
            return self._json({"header": h, "events": ev, "footer": ft})
        if path == "/api/results":
            out = []
            if srv.results_dir.is_dir():
                for f in sorted(srv.results_dir.glob("*.jsonl")):
                    st = f.stat()
                    out.append({"name": f.name, "size": st.st_size, "mtime": st.st_mtime})
            return self._json(out)
        if path.startswith("/api/results/"):
            name = _safe_name(path[len("/api/results/"):], ".jsonl")
            f = srv.results_dir / name
            if not f.is_file():
                raise FileNotFoundError(name)
            rows = []
            with open(f) as fp:
                for line in fp:
                    if line.strip():
                        try:
                            rows.append(json.loads(line))
                        except ValueError:
                            pass
            return self._json({"rows": rows})
        if path == "/api/live":
            return self._live({k: v[0] for k, v in q.items()})
        raise FileNotFoundError(path)

    @staticmethod
    def _list_traces(d: Path) -> list:
        out = []
        if d.is_dir():
            for f in sorted(d.glob("*.trace.jsonl")):
                st = f.stat()
                item = {"name": f.name, "size": st.st_size, "mtime": st.st_mtime}
                try:
                    with open(f) as fp:
                        item.update(_summary(json.loads(fp.readline())))
                except (ValueError, OSError):
                    pass
                out.append(item)
        return out

    # ---- SSE ---------------------------------------------------------
    def _live(self, q: dict):
        cfg_in = dict(q)
        ep = {k: q[k] for k in ("placement", "side", "along") if k in q}
        cfg_in["endpoints"] = ep
        cfg = _parse_cfg(cfg_in)
        delay = max(0.0, min(float(q.get("delay") or 0.01), 2.0))
        topo = _topo(cfg)  # errors before the stream starts -> plain 400
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

        def send(event: str, data):
            msg = f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n".encode()
            try:
                self.wfile.write(msg)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError) as e:
                raise ClientGone from e

        try:
            try:
                send("header", api.trace_header(topo, generator=cfg["generator"],
                                                seed=cfg["seed"], braid=cfg["braid"],
                                                endpoints=cfg["endpoints"], solvers=cfg["solvers"],
                                                size=cfg["size"]))
                tr = StreamTracer(topo.index, lambda e: send("gen", e), delay)
                maze = api.generate(topo, cfg["generator"], cfg["seed"],
                                    params=cfg["gen_params"], endpoints=cfg["endpoints"],
                                    braid=cfg["braid"], tracer=tr)
                send("maze", {"start": topo.index[maze.start], "goal": topo.index[maze.goal]})
                for key in cfg["solvers"]:
                    send("solve-start", {"solver": key})
                    st = StreamTracer(topo.index,
                                      lambda e, key=key: send("solve", {"solver": key, "e": e}),
                                      delay)
                    r = api.solve(maze, key, cfg["seed"], params=cfg["solver_params"], tracer=st)
                    send("solve-end", {"solver": key, "result": _result(maze, r)})
                send("done", {})
            except ClientGone:
                raise
            except Exception as e:  # noqa: BLE001
                msg = (f"not implemented: {e}" if isinstance(e, NotImplementedError)
                       else f"{type(e).__name__}: {e}")
                send("error", {"error": msg})
        except ClientGone:
            pass


class ViewerServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, addr, traces_dir, results_dir):
        super().__init__(addr, Handler)
        self.traces_dir, self.results_dir = Path(traces_dir), Path(results_dir)

    def trace_dirs(self) -> list[Path]:
        """Recorded traces (`mazerunner record`) plus benchmark traces, which the
        bench runner writes next to the results file (results/traces)."""
        return [self.traces_dir, self.results_dir / "traces"]


def make_server(host: str = "127.0.0.1", port: int = 8765, traces_dir: Path = Path("traces"),
                results_dir: Path = Path("results")) -> ViewerServer:
    return ViewerServer((host, port), traces_dir, results_dir)


def serve(host: str = "127.0.0.1", port: int = 8765, traces_dir: Path = Path("traces"),
          results_dir: Path = Path("results"), open_browser: bool = False,
          open_path: str = "/") -> None:
    srv = make_server(host, port, traces_dir, results_dir)
    base = f"http://{host}:{srv.server_address[1]}"
    url = base + (open_path if open_path.startswith("/") else "/" + open_path)
    print(f"MazeRunner viewer on {url}  (Ctrl-C to stop)")
    if open_browser:
        threading.Timer(0.3, webbrowser.open, args=(url,)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
