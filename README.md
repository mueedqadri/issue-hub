# issue-hub

A way of working with coding agents: issues and projects live as markdown in
a git repo next to your code, and many agent sessions can work from it at
once without stepping on each other.

It is a [Claude Code](https://claude.com/claude-code) plugin with one skill.
The skill follows the open [Agent Skills](https://agentskills.io) format, so
other agents that read skills can use it too.

## Why

Agents are good at doing one issue well. They are bad at remembering what the
project is doing, and parallel sessions collide. This hub fixes both with
plain files:

- **A roadmap that holds the state.** `ROADMAP.md` is one page: which branch
  is the mainline, what is in flight, what must be true before the next
  merge, the next five actions, and what is parked on purpose. Every session
  reads it first instead of re-surveying git, and keeps it true.
- **Issue numbers that never collide.** `issue-hub reserve` takes a lock and
  skips any number already used in an issue file, the README, the ledger, or
  a commit or branch in your code repos. Ten sessions can file at once.
- **Issues judged by what the user notices.** Every issue opens with "What
  the user will notice", then cause, fix, and acceptance checks someone else
  can run.
- **Commits and issues point at each other.** Commit subjects start with the
  issue id; the issue's Comments get the hash and a dated note of what was
  verified, with numbers.
- **Projects with an illustrated plan.** Each project has a page with a
  shared contract (how done is judged, how it's checked, the order) and a
  one-page HTML plan.
- **Every page kept in the hub.** Plans, mockups and findings pages are
  saved next to the issue they belong to and linked from its `## Documents`,
  so they outlive published links and scratch folders.
- **Kinds and labels per hub.** Every issue has one Kind (Bug, Feature,
  Improvement or Task by default) and labels from lists the hub keeps in
  `hub.json`, such as its areas. `issue-hub lint` catches anything off-list.
- **House rules travel with the hub.** Each hub's `HUB.md` holds the rules
  only that project has, so a code repo needs no skill of its own: just the
  few lines `init` prints for its AGENTS.md.
- **A local board.** `issue-hub board` serves a kanban view over the files.
  Drag to change status; every write is one line and refuses to overwrite a
  concurrent edit.
- **A fast read-only viewer.** `issue-hub view` is a Linear-style list and
  board with ⌘K, keyboard navigation and an issue panel that shows the
  project's plan and documents. It switches between the hubs of all your
  projects, and [`deploy/`](./deploy) runs it on a server that pulls the
  hubs from git.

The hub is its own git repo, separate from the code, so issue churn never
touches your code history.

## Install

In Claude Code:

```
/plugin marketplace add mueedqadri/issue-hub
/plugin install issue-hub@issue-hub
```

Or copy `skills/issue-hub` into `~/.claude/skills/` (or any agent's skills
folder).

## Start a hub

```sh
issue-hub init ~/notes/myapp-hub --prefix APP --name "My App" --repo ~/code/myapp
```

`issue-hub` lives at `skills/issue-hub/scripts/issue-hub`; inside Claude
Code the skill runs it for you. `init` prints a few lines to paste into your
code repo's `AGENTS.md` or `CLAUDE.md` so every session knows where the hub
is. Then ask your agent to "file an issue for …" or "start a project for …".

Requires Python 3.10+ and git. macOS and Linux (`fcntl` locking).

## Several projects

Give each project its own hub: its own prefix, kinds, labels and house
rules. The viewer shows them side by side:

```sh
issue-hub --hub ~/notes/myapp-hub view ~/notes/other-hub ~/notes/side-project-hub
```

`/` opens the hub you used last; switch with the name at the top left, ⌘K,
or `g` then `h`. To keep the viewer running on a home server or VPS, see
[`deploy/`](./deploy).

## Try the example

[`example/`](./example) is a small hub for a made-up weather app: house rules,
kinds and labels, a roadmap, one project with its plan, and five issues across
every status.

```sh
skills/issue-hub/scripts/issue-hub --hub example board
```

## Commands

| Command | Does |
| --- | --- |
| `init <path> --prefix P [--name N] [--repo R]...` | create a hub |
| `reserve "<title>" [--count N]` | reserve the next number(s) |
| `next` | show the next number without reserving |
| `check <n>` | show every place a number is used |
| `list [-n N]` | recent reservations |
| `where` | the hub, prefix, tracked repos, kinds and labels |
| `lint [--all]` | open issues (or all) missing a Kind or area, or with unknown labels |
| `board [--port N] [--no-open]` | serve the board |

The hub is found from `--hub`, then `$ISSUE_HUB`, then the nearest parent
folder holding `hub.json`.

## Tests

```sh
python3 tests/test_numbers.py
python3 tests/test_board.py
```

## License

MIT
