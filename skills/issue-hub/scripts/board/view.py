#!/usr/bin/env python3
"""Serve the read-only viewer for a hub.

    python3 board/view.py --hub <hub> [--out DIR] [--host 127.0.0.1] [--port 8788]

Exports the hub to DIR (default ~/.cache/issue-hub/<hub name>), serves it,
and re-exports when a hub file changes. Raw hub files are served under
/hub/, never dotfiles or .git. Nothing here writes to the hub.
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export as hubexport  # noqa: E402

_state = {"signature": None, "checked": 0.0}
_lock = threading.Lock()


def signature(root: Path) -> tuple:
    parts = [(root / "hub.json").stat().st_mtime if (root / "hub.json").exists() else 0]
    parts += [(hubexport.VIEWER / name).stat().st_mtime_ns for name in hubexport.VIEWER_FILES]
    for folder in ("issues", "projects", "documents"):
        for entry in os.scandir(root / folder) if (root / folder).is_dir() else ():
            if entry.is_file() and entry.name.endswith(".md"):
                stat = entry.stat()
                parts.append((entry.name, stat.st_mtime_ns, stat.st_size))
    return tuple(parts)


def refresh(root: Path, out: Path) -> None:
    """Re-export at most once a second, and only when a hub file changed."""
    with _lock:
        now = time.monotonic()
        if now - _state["checked"] < 1:
            return
        _state["checked"] = now
        current = signature(root)
        if current != _state["signature"]:
            hubexport.export(root, out)
            _state["signature"] = current


class Handler(SimpleHTTPRequestHandler):
    hub_root: Path
    out: Path

    def log_message(self, fmt: str, *args) -> None:
        pass

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def translate_path(self, path: str) -> str:
        route = unquote(urlparse(path).path)
        if route.startswith("/hub/"):
            relative = route[len("/hub/"):]
            if any(part.startswith(".") for part in relative.split("/")):
                return str(self.out / ".missing")
            target = (self.hub_root / relative).resolve()
            if self.hub_root not in target.parents:
                return str(self.out / ".missing")
            return str(target)
        return super().translate_path(path)

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path in ("/", "/index.html", "/data/index.json"):
            refresh(self.hub_root, self.out)
        super().do_GET()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hub", type=Path, default=Path(os.environ.get("ISSUE_HUB", ".")))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    root = args.hub.expanduser().resolve()
    out = (args.out or Path.home() / ".cache" / "issue-hub" / root.name).expanduser().resolve()
    started = time.monotonic()
    counts = hubexport.export(root, out)
    _state["signature"] = signature(root)
    print(f"exported {counts['issues']} issues, {counts['projects']} projects in {time.monotonic() - started:.1f}s to {out}")

    Handler.hub_root, Handler.out = root, out
    server = ThreadingHTTPServer((args.host, args.port), partial(Handler, directory=str(out)))
    url = f"http://{args.host}:{args.port}/"
    print(f"viewer at {url}")
    if not args.no_open:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
