# ActivityWatch

Self-hosted [ActivityWatch](https://activitywatch.net/) server(s) behind a login-gated gateway,
so multiple people can each get their own isolated instance without exposing anything
unauthenticated to the network.

## Architecture

- `aw-server-<username>` — one plain `aw-server` container per user (built from the root
  [Dockerfile](Dockerfile)), each with its own data volume. Not published to the host —
  only reachable from `aw-gateway` over the internal Docker network.
- `aw-gateway` — a small FastAPI app ([gateway/](gateway/)) that serves a login page,
  and once authenticated, reverse-proxies every request to that user's `aw-server-<username>`.
  Users and password hashes live in a SQLite DB in the `gateway-data` volume.

## Quick start

```bash
cp .env.example .env
# edit .env: set SESSION_SECRET (openssl rand -hex 32)

docker compose up -d --build

# create a login for the "alice" service block already in compose.yml
docker compose exec aw-gateway python -m app.cli create-user alice
```

Visit `http://localhost:5600`, sign in as `alice`, and you'll land on that user's
ActivityWatch dashboard. Point that user's watchers (`aw-client.toml`) at this same
host/port — requests to `/api/...` return `401` instead of redirecting when unauthenticated,
but watchers still need a way to send an authenticated session; the built-in ActivityWatch
watchers don't support login flows, so this setup is best suited to browsing the dashboard
per-user, with watchers reporting directly to each user's own local machine or a
trusted-network instance instead.

## Adding another user

1. In [compose.yml](compose.yml), copy the `aw-server-alice` block, renaming `alice` to
   the new username everywhere (service name and volume name).
2. `docker compose up -d --build`
3. `docker compose exec aw-gateway python -m app.cli create-user <name>`

Manage accounts with `docker compose exec aw-gateway python -m app.cli {create-user,delete-user,list-users}`.
