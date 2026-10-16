# Host the viewer

Run the read-only viewer on a server, so you can browse your hubs from any
device. A small container keeps a copy of each hub fresh from git and serves
the same viewer as `issue-hub view`: about 25 MB of RAM for a thousand issues.

```sh
cp deploy/docker-compose.example.yml deploy/docker-compose.yml
# set HUBS in deploy/docker-compose.yml
mkdir -p deploy/data
docker compose -f deploy/docker-compose.yml up -d --build
```

Then open `http://127.0.0.1:8788`. With several hubs, `/` opens the one you
used last, and the viewer switches between them (`g` then `h`).

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `HUBS` | (required) | Git sources, one per hub, separated by spaces: URLs or paths inside the container |
| `PLUGIN_SOURCE` | the copy in the image | A git source for this plugin, to pick up updates without a rebuild |
| `BRANCH` | `main` | Branch to follow in every repo |
| `SYNC_INTERVAL` | `120` | Seconds between pulls |
| `HOST`, `PORT` | `0.0.0.0`, `8788` | Where the viewer listens inside the container |

## Private hubs

- **A git server on the same machine:** mount its bare repositories read-only
  and list their paths in `HUBS`, for example `/repos/my-hub.git`. No token
  is needed.
- **A hosted repo:** use a read-only token in the URL
  (`https://<user>:<token>@host/you/hub.git`). Treat the compose file as a
  secret then, and prefer a token limited to that one repo.

## Keep it private

The viewer has no login, and it shows everything in your hubs. Bind it to
localhost, or reach it through a VPN or a tailnet. To give it its own
Tailscale name, run a `tailscale/tailscale` sidecar with
`network_mode: service:<sidecar>` on the board, set `HOST=127.0.0.1`, and
point the sidecar's serve config at `http://127.0.0.1:8788`.

Nothing in the container writes to your hubs; edits still happen in the
working copies where your agents run.
