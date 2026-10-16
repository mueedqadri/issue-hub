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


def run_status(env: dict[str, str], *args: str) -> tuple[int, str]:
    result = subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def issue(hub: Path, name: str, status: str, kind: str | None, labels: str) -> None:
    kind_line = f"- **Kind:** {kind}\n" if kind is not None else ""
    (hub / "issues" / f"{name}.md").write_text(
        f"# {name}: Test\n\n## Metadata\n- **Status:** {status}\n{kind_line}- **Labels:** {labels}\n\n## Description\n\nBody.\n")


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


def lint_hub(root: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k != "ISSUE_HUB"}
    run(env, "init", str(root), "--prefix", "LNT")
    config = json.loads((root / "hub.json").read_text())
    config["labels"] = {"area": ["Reader", "Audio"], "platform": ["iOS"]}
    config["lint_from"] = 3
    (root / "hub.json").write_text(json.dumps(config))
    env = dict(env, ISSUE_HUB=str(root))
    issue(root, "LNT-1", "Backlog", None, "None")                  # before lint_from: ignored
    issue(root, "LNT-3", "Backlog", "Bug", "Reader, iOS")         # clean
    issue(root, "LNT-4", "Todo", None, "Reader")                  # no Kind
    issue(root, "LNT-5", "In Progress", "Chore", "Audio")         # Kind not on the list
    issue(root, "LNT-6", "Backlog", "Task", "iOS")                # no area
    issue(root, "LNT-7", "Backlog", "Feature", "Reader, Shiny")   # unknown label
    issue(root, "LNT-8", "Done", None, "None")                    # closed: only with --all
    code, out = run_status(env, "lint")
    check(code == 1, "lint should fail when open issues need attention")
    check("LNT-1" not in out, "lint should skip issues before lint_from")
    check(not any(line.startswith("LNT-3:") for line in out.splitlines()), "a clean issue should not be reported")
    check("LNT-4: no Kind" in out, "a missing Kind should be reported")
    check("LNT-5: Kind 'Chore' is not one of" in out, "a Kind off the list should be reported")
    check("LNT-6: no area label" in out, "a missing area should be reported")
    check("LNT-7: unknown label 'Shiny'" in out, "an unknown label should be reported")
    check("LNT-8" not in out, "closed issues are skipped by default")
    check("5 open issues from LNT-3 checked; 4 need attention." in out, f"lint summary was: {out.splitlines()[-1]}")
    code, out = run_status(env, "lint", "--all")
    check("LNT-8: no Kind; no area label" in out, "--all should include closed issues")
    for name in ("LNT-4", "LNT-5", "LNT-6", "LNT-7", "LNT-8"):
        (root / "issues" / f"{name}.md").unlink()
    code, out = run_status(env, "lint")
    check(code == 0, f"lint should pass once only clean issues remain: {out}")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        hub, env = make_world(Path(tmp))

        config = json.loads((hub / "hub.json").read_text())
        check(config["prefix"] == "ABC", "init should upper-case the prefix")
        check((hub / "ROADMAP.md").exists() and (hub / ".git").exists(), "init should write ROADMAP.md and a git repo")
        check("{{" not in (hub / "README.md").read_text(), "init should fill every README placeholder")
        check((hub / "HUB.md").exists() and "{{" not in (hub / "HUB.md").read_text(), "init should write a filled HUB.md")
        check(config["kinds"] == ["Bug", "Feature", "Improvement", "Task"], "init should list the default kinds")
        check("- **Kind:**" in (hub / "templates" / "issue.md").read_text(), "the issue template should carry Kind")

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

        lint_hub(Path(hub).parent / "linted")

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
