#!/usr/bin/env python3
"""Checks for issue-hub's init and number reservation.

    python3 tests/test_numbers.py

Runs against a throwaway hub and code repo in a temp directory.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "issue-hub" / "scripts" / "issue-hub"
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        FAILURES.append(message)


def run(env: dict[str, str], *args: str, cwd: Path | None = None) -> str:
    result = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def make_world(root: Path) -> tuple[Path, dict[str, str]]:
    app = root / "app"
    app.mkdir()
    git(app, "init", "-q")
    git(app, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "ABC-15: Commit only")
    git(app, "branch", "someone/abc-17-branch-only")

    env = {k: v for k, v in os.environ.items() if k != "ISSUE_HUB"}
    hub = root / "hub"
    run(env, "init", str(hub), "--prefix", "abc", "--name", "Test", "--repo", str(app))
    (hub / "issues" / "ABC-10.md").write_text("# ABC-10\n")
    (hub / "issues" / "XYZ-90.md").write_text("# XYZ-90: another prefix\n")
    with open(hub / "README.md", "a") as readme:
        readme.write("- [ABC-12](./issues/ABC-12.md) listed, file missing\n")
    return hub, dict(env, ISSUE_HUB=str(hub))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        hub, env = make_world(Path(tmp))

        config = json.loads((hub / "hub.json").read_text())
        check(config["prefix"] == "ABC", "init should upper-case the prefix")
        check((hub / "ROADMAP.md").exists() and (hub / ".git").exists(), "init should write ROADMAP.md and a git repo")
        check("{{" not in (hub / "README.md").read_text(), "init should fill every README placeholder")

        check(run(env, "next") == "ABC-18", "next should clear the branch-only ABC-17")
        check(run(env, "reserve", "First") == "ABC-18", "first reservation should be 18")
        check(run(env, "next") == "ABC-19", "the ledger should hold 18")
        check(run(env, "reserve", "--count", "3", "Phases") == "ABC-19 ABC-20 ABC-21", "--count should give a run")
        check("taken" in run(env, "check", "ABC-15"), "a commit-only number is taken")
        check("taken" in run(env, "check", "12"), "a README-only number is taken")
        check("free" in run(env, "check", "99"), "an unused number is free")
        check("free" in run(env, "check", "90"), "another prefix's number is not taken")

        bare = {k: v for k, v in env.items() if k != "ISSUE_HUB"}
        check(run(bare, "next", cwd=hub / "issues") == "ABC-22", "the hub should be found from a subfolder")

        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(lambda i: run(env, "reserve", f"Race {i}"), range(20)))
        numbers = [int(n.split("-")[1]) for n in results]
        check(len(set(numbers)) == 20, f"concurrent reservations collided: {sorted(numbers)}")
        check(sorted(numbers) == list(range(22, 42)), f"concurrent reservations left gaps: {sorted(numbers)}")

        try:
            run(env, "init", str(hub), "--prefix", "ABC")
            check(False, "init should refuse an existing hub")
        except RuntimeError:
            pass

    if FAILURES:
        print("FAIL")
        for failure in FAILURES:
            print(f"  - {failure}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
