# {{NAME}} hub rules

House rules for this hub, on top of the issue-hub skill. Agents read this file
before filing or changing issues. Keep it short; delete any section you don't
need.

## Kinds and labels

The lists live in `hub.json`. Every issue gets one Kind and at least one area
label. Add a platform or focus label only when the issue is about it.

## Commits and branches

- Commit subject: `{{PREFIX}}-<n>: <imperative summary>`, at most 72 characters.
- Branch: `<user>/{{prefix}}-<n>-<slug>`.

## Things never to do

- (for example: a script that must never be re-run, a folder never to edit)
