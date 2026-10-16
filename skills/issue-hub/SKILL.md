---
name: issue-hub
description: Track work as markdown issues and projects in a local issue hub (a git repo of one file per issue, plus a ROADMAP.md that holds the project's state) that many agent sessions share safely. Use when asked to file an issue, reserve an issue number, start a project, move an issue's status, link a commit to an issue, update the roadmap, open the board, or set up a new hub. Not for GitHub Issues, Jira or hosted Linear.
license: MIT
---

# Issue hub

The hub is a plain git repo of markdown, separate from the code:

```
<hub>/
  hub.json             prefix, tracked code repos, and the hub's kinds and labels
  HUB.md               this hub's house rules; read it before any change
  ROADMAP.md           the state of the project on one page
  README.md            index of projects and of every issue by status
  issues/<P>-<n>.md    one file per issue
  projects/<slug>.md   project pages; <slug>.html is the illustrated plan
  documents/           notes, interviews, reviews the issues cite
  templates/           issue.md and project.md to copy
  reservations.tsv     ledger of every number handed out
```

Every command below is `${CLAUDE_SKILL_DIR}/scripts/issue-hub`. Find the hub
from the code repo's AGENTS.md or CLAUDE.md, or `$ISSUE_HUB`, and pass it as
`--hub <path>` unless you are working inside it. `issue-hub where` confirms
the hub, prefix and tracked repos.

## Before any work

Read the hub's `HUB.md`. It holds the rules this hub adds on top of this
skill (things never to do, commit and branch names, how releases work), and
they win where they differ. Then read `ROADMAP.md`. It says which branch is the mainline, what is in flight,
what is parked on purpose and what to do next. Trust it over your own survey
of git, but check the date on each section; if a fact is stale, fix the
roadmap as part of your work.

Issues, plans and roadmaps describe intent. The code is the truth. Check the
code before acting on what a page says.

## File an issue

1. Reserve the number. Never pick one by hand:
   `issue-hub reserve "<title>"` prints e.g. `ABC-42`;
   `--count N` reserves a run for a project's phases.
   It locks the ledger and skips every number already used in an issue file,
   the README, the ledger, or a commit or branch in any tracked repo. That is
   what lets parallel sessions file at the same time without colliding.
   `issue-hub check <n>` lists where a number appears.
2. Copy `templates/issue.md` to `issues/<P>-<n>.md` and fill it in:
   - The title is imperative and says what will be true when done.
   - **What the user will notice** comes first, in the user's words. It is
     how the issue is judged done.
   - Cause, Fix, Acceptance. Acceptance is checks someone else can run.
   - Status starts at Backlog unless work starts now.
   - **Kind** is exactly one of the hub's kinds (`issue-hub where` lists
     them; by default Bug, Feature, Improvement, Task). It can change later
     as you learn more.
   - **Labels** come only from the lists in `hub.json`: at least one `area`,
     plus a `platform` or `focus` label only when the issue is about it. If
     nothing fits, say so to the user rather than inventing a label.
3. Add the issue's line under its status in `README.md`'s Issues Overview.
4. If it belongs to a project, link it from the project page's Issues list
   and from the issue's Relationships.
5. Run `issue-hub lint`. It lists open issues missing a Kind or an area, or
   using a label that isn't in `hub.json`; fix your own before committing.
6. Commit in the hub repo: `git -C <hub> add issues/<P>-<n>.md README.md ...`.
   `git show --stat` must list the issue file as added, not modified; if it
   says modified, someone else holds that number. Stop and reserve again.

File every problem you find as its own issue, even if you only fix one now.

## Work an issue

- One issue per logical change. Commit subject: `<P>-<n>: <imperative
  summary>`, at most 72 characters; the body says what changed and why.
- Branch: `<user>/<p>-<n>-<slug>` (lower-case prefix). A project gets its own
  branch off main; each issue branches off the project branch and merges back
  with `--no-ff`.
- Move Status as work moves: Backlog → Todo → In Progress → In Review →
  Done (or Canceled, with the reason). Move the README line at the same time.
- After each commit in the code repo, add under the issue's `## Comments`:
  the short hash and subject, then a dated note saying where it landed and
  what was verified, with numbers (tests passed and failed, devices checked).
  Write what you saw, not what you expect.
- Commit hub changes in the hub repo, never in the code repo.
- Finish one issue and get it reviewed before starting the next, unless the
  user says otherwise.

## Start a project

1. Reserve one number per phase with `issue-hub reserve --count N "<project>"`.
2. Copy `templates/project.md` to `projects/<slug>.md`. Fill in why the
   project exists, the shared contract (how each issue is judged done, how it
   is checked, the order), and the issue list. Add a row to README's
   Projects table.
3. Write `projects/<slug>.html`: one self-contained, theme-aware page with
   why the project exists, a diagram where it helps, the tasks, and for every
   task its "What the user will notice". If you can publish pages (for
   example as an Artifact), publish it and link the URL from the project's
   `## Documents` next to the file. Check old links still work before relying
   on them.
4. When scope changes, update the page and republish to the same URL.

## Keep the roadmap true

Update `ROADMAP.md` when a branch merges, a project starts or ends, a gate
changes, or something is parked. Change the "Last verified" date only for
the sections you actually checked.

## Sharing the hub with other sessions

Several sessions may edit the hub at once.

- Reserve numbers only through `issue-hub reserve`.
- Stage only your own files and hunks (`git add -p`); README.md and the
  ledger are shared, so never `git add -A` or revert someone else's lines.
- Never read and rewrite a whole shared file in one step from a stale copy;
  re-read it right before editing.

## The board

`issue-hub board` serves the hub at http://127.0.0.1:8787: columns by
status, Kind, project and label filters, every page rendered, with each
issue's Kind as a colored badge. Dragging a card or
adding a comment rewrites exactly one line and refuses the write if the file
changed on disk since it loaded. Standard-library Python, nothing to install.

## Set up a new hub

`issue-hub init <path> --prefix ABC --name "<Project>" --repo <code repo>`
creates the folders, `hub.json`, `HUB.md`, README, ROADMAP, templates and the
ledger, runs `git init`, and prints the lines to add to the code repo's
AGENTS.md or CLAUDE.md. Pass `--repo` once per code repo whose commits and
branches carry issue numbers. Then, with the user, fill in `hub.json`'s
`labels` (`area` first) and the house rules in `HUB.md`, and commit the hub.

A hub adopting kinds and labels midway can set `"lint_from": <n>` in
`hub.json` so `lint` only checks issues from that number on.
