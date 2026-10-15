## Issue tracking and commits

Issues are local markdown in `{{HUB}}` (its own git repo).
`{{PREFIX}}-<n>` refers there. Its `ROADMAP.md` is the state of the project;
read it before re-surveying git. Use the `issue-hub` skill to file issues,
move status, link commits and start projects.

- One issue per logical change. Subject `{{PREFIX}}-<n>: <imperative summary>`,
  at most 72 characters. The body says what changed and why.
- Branches: `<your-name>/{{prefix}}-<n>-<slug>`.
- After committing, add the short hash and subject under the issue's
  `## Comments` and keep its status current. Hub changes are committed in the
  hub repo, never here.
