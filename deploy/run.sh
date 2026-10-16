#!/bin/sh
# Keeps read-only copies of one or more issue hubs (and, optionally, the
# issue-hub plugin) fresh from git, and serves the viewer for all of them.
#
#   HUBS            space-separated git sources, one per hub: URLs or paths (required)
#   PLUGIN_SOURCE   git source for the plugin; unset uses the copy in this image
#   BRANCH          branch to follow in every repo (default main)
#   SYNC_INTERVAL   seconds between pulls (default 120)
#   HOST, PORT      where the viewer listens (default 0.0.0.0:8788)
#   DATA            working folder (default /data)
#
# The viewer re-exports a hub whenever its files change; a plugin update
# restarts the viewer.
set -eu

: "${HUBS:?set HUBS to one or more git sources}"
INTERVAL=${SYNC_INTERVAL:-120}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8788}
BRANCH=${BRANCH:-main}
DATA=${DATA:-/data}
export HOME="$DATA/home"
mkdir -p "$HOME" "$DATA/hubs"
git config --global safe.directory '*'

sync() {
  if [ -d "$2/.git" ]; then
    git -C "$2" fetch -q origin "$BRANCH" && git -C "$2" reset -q --hard "origin/$BRANCH"
  else
    git clone -q --branch "$BRANCH" "$1" "$2"
  fi
}

folder() { echo "$DATA/hubs/$(basename "$1" .git)"; }
plugin_dir() { if [ -n "${PLUGIN_SOURCE:-}" ]; then echo "$DATA/plugin"; else echo /app; fi; }
plugin_rev() { git -C "$(plugin_dir)" rev-parse --short HEAD 2>/dev/null || echo image; }

sync_all() {
  for src in $HUBS; do
    sync "$src" "$(folder "$src")" || echo "sync failed for $(basename "$src" .git)" >&2
  done
  if [ -n "${PLUGIN_SOURCE:-}" ]; then
    sync "$PLUGIN_SOURCE" "$DATA/plugin" || echo "plugin sync failed" >&2
  fi
}

start() {
  set --
  for src in $HUBS; do set -- "$@" --hub "$(folder "$src")"; done
  python3 -B "$(plugin_dir)/skills/issue-hub/scripts/board/view.py" "$@" \
    --out "$DATA/site" --host "$HOST" --port "$PORT" --no-open &
  PID=$!
  REV=$(plugin_rev)
  echo "viewer started on $HOST:$PORT for $(echo $HUBS | wc -w) hub(s), plugin $REV"
}

sync_all
trap 'kill "$PID" 2>/dev/null; exit 0' TERM INT
start

while sleep "$INTERVAL" & wait $!; do
  sync_all
  if [ "$(plugin_rev)" != "$REV" ] || ! kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
    start
  fi
done
