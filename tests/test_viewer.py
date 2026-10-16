#!/usr/bin/env python3
"""Checks for the read-only viewer: the export and the server.

    python3 tests/test_viewer.py

Exports the example hub into a temp directory (never writes to the hub), then
serves a throwaway copy and checks what the server will and won't hand out.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "issue-hub" / "scripts"
sys.path.insert(0, str(SCRIPTS / "board"))

import export as hubexport  # noqa: E402

HUB = ROOT / "example"
FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        FAILURES.append(f"{label}{' — ' + detail if detail else ''}")
        print(f"  FAIL {label}{' — ' + detail if detail else ''}")


def fetch(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=5) as res:
            return res.status, res.read()
    except urllib.error.HTTPError as err:
        return err.code, b""


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "site"

        print("exporting the example hub")
        counts = hubexport.export(HUB, out)
        check("every issue exported", counts["issues"] == 5, str(counts))
        index = json.loads((out / "data" / "index.json").read_text())
        check("index carries kinds and label groups", index["kinds"] and "area" in index["labelGroups"])
        check("index lists ROADMAP and HUB pages", index["pages"] == ["ROADMAP.md", "HUB.md"], str(index["pages"]))
        check("cards are slim", "body" not in index["issues"][0] and "mtime" not in index["issues"][0])
        check("cards carry dates", all(i["created"] and i["updated"] for i in index["issues"]))
        project = next(p for p in index["projects"] if p["slug"] == "offline-forecasts")
        check("project names its illustrated plan", project["plan"] == "projects/offline-forecasts.html")
        check("project counts its issues", project["total"] == 3, str(project["counts"]))
        pw2 = json.loads((out / "data" / "issues" / "PW-2.json").read_text())
        check("relations get their inverse", {"rel": "Blocked by", "id": "PW-1"} in pw2["relations"], str(pw2["relations"]))
        check("pages link raw files under hub/", "/raw/" not in pw2["html"] and 'href="/projects/' not in pw2["html"])
        check("viewer files copied", all((out / name).exists() for name in hubexport.VIEWER_FILES))
        check("documents exported", (out / "data" / "docs" / "offline-usage-interviews.json").exists())
        check("ROADMAP page exported", (out / "data" / "pages" / "ROADMAP.md.json").exists())

        again = hubexport.export(HUB, out)
        check("an unchanged hub rewrites nothing", again["changed"] == 0, str(again))

        print("removing an issue from a copy")
        copy = Path(tmp) / "hub"
        shutil.copytree(HUB, copy)
        (copy / "issues" / "PW-5.md").unlink()
        gone = hubexport.export(copy, out)
        check("a deleted issue's page is removed", gone["removed"] == 1 and not (out / "data" / "issues" / "PW-5.json").exists(), str(gone))

        print("serving the copy")
        (copy / ".git").mkdir(exist_ok=True)
        (copy / ".git" / "config").write_text("secret")
        (copy / ".env").write_text("secret")
        port = free_port()
        server = subprocess.Popen([sys.executable, str(SCRIPTS / "board" / "view.py"), "--hub", str(copy), "--out", str(out),
                                   "--port", str(port), "--no-open"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(50):
                try:
                    socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                    break
                except OSError:
                    time.sleep(0.1)
            status, body = fetch(base + "/")
            check("serves the viewer", status == 200 and b"viewer.js" in body, str(status))
            status, body = fetch(base + "/data/index.json")
            check("serves the index", status == 200 and json.loads(body)["prefix"] == "PW", str(status))
            status, _ = fetch(base + "/hub/projects/offline-forecasts.html")
            check("serves the hub's illustrated plan", status == 200, str(status))
            check("refuses .git", fetch(base + "/hub/.git/config")[0] == 404)
            check("refuses dotfiles", fetch(base + "/hub/.env")[0] == 404)
            check("refuses paths outside the hub", fetch(base + "/hub/%2e%2e/%2e%2e/etc/hosts")[0] == 404)
            last = urllib.request.urlopen(base + "/data/index.json", timeout=5).headers["Last-Modified"]
            check("an unchanged index revalidates as 304", fetch(base + "/data/index.json", {"If-Modified-Since": last})[0] == 304)

            (copy / "issues" / "PW-1.md").write_text((copy / "issues" / "PW-1.md").read_text().replace("**Status:** Done", "**Status:** Todo", 1))
            time.sleep(1.1)
            status, body = fetch(base + "/data/index.json")
            pw1 = next(i for i in json.loads(body)["issues"] if i["id"] == "PW-1")
            check("an edited issue shows up without a restart", pw1["status"] == "Todo", pw1["status"])
        finally:
            server.terminate()
            server.wait(timeout=5)

    if shutil.which("node"):
        result = subprocess.run(["node", "--check", str(SCRIPTS / "viewer" / "viewer.js")], capture_output=True, text=True)
        check("viewer.js parses", result.returncode == 0, result.stderr.strip())

    if FAILURES:
        print(f"\n{len(FAILURES)} failed")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
