"""
Design System Carousel Creator -- preview server.

    python serve.py                     # inside a project: serve dist/, open the canvas
    python serve.py --dir some/dir      # serve any bundle
    python serve.py --no-open --port 8080
    python serve.py --watch             # rebuild on change, push reload to the canvas

The bundle REQUIRES a same-origin server to work at all: over file:// the browser
gives the iframe an opaque origin, so the theme bridge, the card index and the audit
overlay are all blocked. A canvas document with no way to start a server for it
reads as "nothing pans or zooms," which is a script failure only in appearance.

Three things this adds over `python -m http.server`:

  free-port selection    "Address already in use" is not an error worth showing a
                         designer. Try the port, then walk up.
  /__dscc/events        Server-Sent Events. The watcher polls mtimes; on a change
                         it runs the project's builder and emits `reload`. The
                         canvas restores scale, position, theme and focus across it.
  /__dscc/state         project.json + the latest scorecard, so the canvas audit
                         overlay can read outside dist/ -- deliberately, read-only,
                         and only while this server is running. The bundle itself
                         stays self-contained: on a plain static server those two
                         routes 404 and the canvas degrades to pan/zoom/theme.

Plus no-cache headers, because http.server serving a stale .js you just rebuilt is
a genuinely confusing ten minutes.
"""
from __future__ import annotations

import argparse
import http.server
import json
import pathlib
import queue
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import project as proj  # noqa: E402

WATCH_EXTS = {".py", ".json", ".css", ".js", ".html", ".md"}
POLL_SECONDS = 0.6

_clients: "list[queue.Queue[str]]" = []
_clients_lock = threading.Lock()


def broadcast(event: str) -> None:
    with _clients_lock:
        dead = []
        for q in _clients:
            try:
                q.put_nowait(event)
            except Exception:
                dead.append(q)
        for q in dead:
            _clients.remove(q)


class Handler(http.server.SimpleHTTPRequestHandler):
    project_dir: pathlib.Path | None = None
    quiet = False

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "text/javascript", ".mjs": "text/javascript",
        ".json": "application/json", ".css": "text/css",
        ".svg": "image/svg+xml", ".woff2": "font/woff2", ".woff": "font/woff",
        ".otf": "font/otf", ".ttf": "font/ttf", ".webp": "image/webp",
        ".avif": "image/avif", ".map": "application/json",
    }

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        if self.quiet:
            return
        code = args[1] if len(args) > 1 else ""
        # A 404 on .image-slots.state.json is the documented first-load state of a
        # generated sidecar; saying so beats letting it read as a broken build.
        path = args[0] if args else ""
        if ".image-slots.state.json" in str(path) and str(code) == "404":
            sys.stderr.write("  · .image-slots.state.json 404 — generated sidecar, "
                             "not authored. Harmless.\n")
            return
        if str(code).startswith("2") or str(code).startswith("3"):
            return
        sys.stderr.write(f"  ! {args[0] if args else ''} {code}\n")

    # ---- routes ----------------------------------------------------------
    def do_GET(self):  # noqa: N802
        route = urllib.parse.urlparse(self.path).path
        if route.endswith("/__dscc/events"):
            return self._sse()
        if route.endswith("/__dscc/state"):
            return self._state()
        if route.endswith("/__dscc/ping"):
            return self._json({"ok": True, "at": time.time()})
        return super().do_GET()

    def _json(self, obj: dict, code: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _state(self) -> None:
        d = self.project_dir
        if not d:
            return self._json({"project": None, "scorecard": None})
        out: dict = {"project": None, "scorecard": None, "history": []}
        try:
            man = proj.load(d)
            out["project"] = man
            sc = proj.path_of(d, man, "scorecard")
            if sc and sc.exists():
                out["scorecard"] = json.loads(sc.read_text(encoding="utf-8"))
            out["history"] = proj.read_history(d)[-30:]
        except Exception as e:
            out["error"] = f"{type(e).__name__}: {e}"
        self._json(out)

    def _sse(self) -> None:
        q: "queue.Queue[str]" = queue.Queue()
        with _clients_lock:
            _clients.append(q)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(b"retry: 1500\n\n")
            self.wfile.flush()
            while True:
                try:
                    ev = q.get(timeout=15)
                    self.wfile.write(f"event: {ev}\ndata: {int(time.time())}\n\n"
                                     .encode("utf-8"))
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")   # proxies drop idle streams
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def free_port(preferred: int, tries: int = 40) -> int:
    for p in range(preferred, preferred + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return preferred


# ─────────────────────────────────────────────────────────────────── watch ──
def snapshot(paths: list[pathlib.Path]) -> dict[str, float]:
    out: dict[str, float] = {}
    for root in paths:
        if not root.exists():
            continue
        if root.is_file():
            out[str(root)] = root.stat().st_mtime
            continue
        for f in root.rglob("*"):
            if f.is_file() and f.suffix.lower() in WATCH_EXTS and \
               "__pycache__" not in f.parts:
                try:
                    out[str(f)] = f.stat().st_mtime
                except OSError:
                    pass
    return out


def watcher(paths: list[pathlib.Path], builder: pathlib.Path | None,
            stop: threading.Event) -> None:
    prev = snapshot(paths)
    while not stop.wait(POLL_SECONDS):
        cur = snapshot(paths)
        changed = [k for k, v in cur.items() if prev.get(k) != v]
        gone = [k for k in prev if k not in cur]
        if not changed and not gone:
            continue
        prev = cur
        names = ", ".join(pathlib.Path(c).name for c in changed[:3])
        print(f"\n  change: {names}{' …' if len(changed) > 3 else ''}")
        if builder and builder.exists() and \
           any(pathlib.Path(c).suffix in (".py", ".json") for c in changed):
            print(f"  rebuilding via {builder.name} …", end="", flush=True)
            t0 = time.time()
            r = subprocess.run([sys.executable, str(builder)], cwd=str(builder.parent),
                               capture_output=True, text=True)
            if r.returncode == 0:
                print(f" ok ({time.time() - t0:.1f}s)")
            else:
                print(" FAILED")
                tail = (r.stderr or r.stdout or "").strip().splitlines()[-8:]
                for line in tail:
                    print(f"    {line}")
                broadcast("audit")           # let the canvas surface the failure state
                continue
        broadcast("reload")


# ──────────────────────────────────────────────────────────────────── main ──
def serve(directory: pathlib.Path, *, port: int = 4173, open_browser: bool = True,
          page: str = "canvas.html", watch: bool = False,
          project_dir: pathlib.Path | None = None,
          watch_paths: list[pathlib.Path] | None = None,
          builder: pathlib.Path | None = None, quiet: bool = False) -> int:
    directory = directory.resolve()
    if not directory.is_dir():
        print(f"nothing to serve: {directory}")
        return 1

    target = directory / page
    if not target.exists():
        alt = sorted(directory.glob("*.dc.html"))
        if alt:
            print(f"  ! {page} missing — falling back to {alt[0].name}")
            print(f"    (run scaffold.py canvas \"{directory}\" to install the host)")
            page = alt[0].name
        else:
            print(f"  ! neither {page} nor any .dc.html found in {directory}")

    port = free_port(port)
    Handler.project_dir = project_dir
    Handler.quiet = quiet

    def factory(*a, **kw):
        return Handler(*a, directory=str(directory), **kw)

    stop = threading.Event()
    threads: list[threading.Thread] = []
    if watch:
        paths = watch_paths or [directory]
        t = threading.Thread(target=watcher, args=(paths, builder, stop), daemon=True)
        t.start()
        threads.append(t)

    url = f"http://127.0.0.1:{port}/{urllib.parse.quote(page)}"
    with Server(("127.0.0.1", port), factory) as httpd:
        print(f"\n  serving  {directory}")
        if project_dir:
            print(f"  project  {project_dir.name}  (audit overlay live)")
        if watch:
            print(f"  watching {', '.join(p.name for p in (watch_paths or [directory]))}"
                  + (f" → {builder.name}" if builder else ""))
        print(f"\n  {url}\n")
        print("  drag to pan · ⌘/ctrl+scroll to zoom · D theme · I index · A audit · ? keys")
        print("  ctrl-c to stop\n")
        if open_browser:
            threading.Timer(0.35, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  stopped")
        finally:
            stop.set()
            for t in threads:
                t.join(timeout=1.0)
    return 0


def resolve_target(args) -> tuple[pathlib.Path, pathlib.Path | None, list[pathlib.Path], pathlib.Path | None]:
    """Work out what to serve. Inside a project, everything comes from the manifest."""
    if args.dir:
        d = pathlib.Path(args.dir).resolve()
        return d, proj.find_project(d), [d], None

    pd = proj.find_project()
    if not pd:
        d = pathlib.Path(".").resolve()
        print("  ! not inside a Creator project — serving the current directory")
        return d, None, [d], None

    man = proj.load(pd)
    dist = pd / man["layout"]["dist"]
    build = pd / man["layout"]["build"]
    builder = proj.path_of(pd, man, "builder")
    return dist, pd, [build, dist], builder


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=None, help="serve this directory instead of the project bundle")
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--page", default="canvas.html")
    ap.add_argument("--no-open", action="store_true", dest="no_open")
    ap.add_argument("--watch", action="store_true",
                    help="rebuild via build/build.py on change and push reload")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    directory, pd, paths, builder = resolve_target(a)
    port = a.port
    open_browser = not a.no_open
    if pd and port is None:
        try:
            s = proj.load(pd).get("serve") or {}
            port = s.get("port", 4173)
            if s.get("open") is False:
                open_browser = False
        except Exception:
            port = 4173
    sys.exit(serve(directory, port=port or 4173, open_browser=open_browser,
                   page=a.page, watch=a.watch, project_dir=pd,
                   watch_paths=paths, builder=builder, quiet=a.quiet))


if __name__ == "__main__":
    main()
