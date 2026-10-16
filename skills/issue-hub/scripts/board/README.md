# Board

A local board over an issue hub. Read every project, issue and document; drag
issues between columns to change their status.

```sh
issue-hub board            # or: python3 serve.py --hub <path>
```

Opens `http://127.0.0.1:8787` (`--port N`, `--no-open`). Standard-library
Python only: no packages, no build step. It re-reads `issues/`, `projects/`
and `documents/` when they change on disk, so the board is never stale.

## What it shows

- **Board**: six columns (Backlog, Todo, In Progress, In Review, Done,
  Canceled). Done and Canceled start folded. Search with `/`. Kind, project
  and label filters are searchable multi-selects, and each card shows its
  Kind as a colored badge.
- **Projects**: one card per project with live issue counts, newest first.
  The issue list is derived from the issue files. A `projects/<slug>.html`
  plan opens from the header.
- **Documents**: the pages under `documents/`.

Links between issues, projects and documents navigate inside the board, and
the URL hash (`#ABC-12`, `#project/<slug>`) makes back and forward work.

## What it writes

| Action | Effect on disk |
| --- | --- |
| Drag a card, or change Status | rewrites the `- **Status:**` line |
| Priority | rewrites the `- **Priority:**` line |
| Project | rewrites the `- **Project:**` line |
| Add comment | appends `**YYYY-MM-DD** — …` under `## Comments` |

Every write replaces one line (or appends one block) through a temp file and
`os.replace`, and is refused with a 409 if the file changed on disk since the
board loaded it, so a concurrent edit by a person or an agent is never lost.
After a status or project change it rebuilds only README's
`## Issues Overview` block. The hub is a git repo, so `git diff` shows every
byte the board touched.

Files exported from Linear (`Done (completed)`, blockquote comments) keep
their dialect after an edit.

The board does not create issues: numbers come from `issue-hub reserve`.

## The read-only viewer

```sh
issue-hub view                 # live, re-exports when a file changes
issue-hub export <dir>         # static site for any web server
```

`view` exports to `~/.cache/issue-hub/<hub>` and serves it at
`http://127.0.0.1:8788` (`--host`, `--port`, `--out`, `--no-open`). The
export holds `data/index.json` (every card, project and document, about
60 KB compressed for 1,000 issues) and one pre-rendered JSON page per issue,
project and document. Files whose content is unchanged are not rewritten.
Whatever serves the export must also serve the hub checkout at `hub/`,
refusing dotfiles, for plans, images and documents.

The viewer keeps the index in memory and in the browser, so it draws from
the last copy at once and checks for a newer one in the background. Filters,
search and grouping run in the browser. Keys: ⌘K, `/`, `f`, `j`/`k`, Enter,
Esc, `b`, `g` then `a`/`b`/`l`/`d`/`p`, `p` for the project plan, `c` to copy
a link, `?` for the list. Colors follow the theme in `dashboard-theme`.

## Files

| File | Role |
| --- | --- |
| `serve.py` | entry point and HTTP API; binds `127.0.0.1` only |
| `parse.py` | hub → dicts, and the single-line writers |
| `render.py` | a markdown subset → HTML, and hub link rewriting |
| `ui.html` | the whole UI: inline CSS and vanilla JS |
| `export.py` | hub → static viewer site (JSON and pre-rendered pages) |
| `view.py` | serves an export and the hub's files, read-only |
| `../viewer/` | the read-only viewer: `index.html`, `viewer.css`, `viewer.js` |

`render.py` is a deliberate subset of markdown: headings, paragraphs,
emphasis, code, nested lists, blockquotes, tables, rules, links and images.
The parser reads only each file's `## Metadata` list and renders the rest
verbatim.
