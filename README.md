# ActivityWatch

Self-hosted [ActivityWatch](https://activitywatch.net/) server(s) behind a login-gated gateway,
so multiple people can each get their own isolated instance without exposing anything
unauthenticated to the network.

## Architecture

- `aw-server-<username>` — one plain `aw-server` container per user (built from the root
  [Dockerfile](Dockerfile)), each with its own data volume. Not published to the host —
  only reachable from `aw-gateway` over the internal Docker network.
- `aw-gateway` — a Django app ([gateway/](gateway/)) that serves a login page, and once
  authenticated, reverse-proxies every request to that user's `aw-server-<username>`. Users
  can sign in with a local password and/or (if configured) via an existing Authentik instance
  over OIDC — either way, a user only gets proxied through if they're explicitly provisioned
  (see "Adding another user" below); Authentik authenticating someone isn't enough on its own.

## Quick start

```bash
cp .env.example .env
# edit .env: set DJANGO_SECRET_KEY (openssl rand -hex 32)

docker compose up -d --build

# create a login for the "alice" service block already in compose.yml
docker compose exec aw-gateway python scripts/create_user.py alice
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
3. `docker compose exec aw-gateway python scripts/create_user.py <name>`

Manage accounts with `docker compose exec aw-gateway python scripts/{create_user,delete_user,list_users}.py`.

## Optional: login via Authentik

If you already run Authentik elsewhere, you can offer it as a second login option alongside
the local username/password form:

1. In Authentik, create an OAuth2/OIDC **Provider** (type: OAuth2/OpenID) and an
   **Application** using it for this instance.
2. Set its redirect URI to `http://<this-host>:5600/login/authentik/callback/`.
3. In `.env`, fill in `AUTHENTIK_ISSUER` (your Authentik instance's base URL),
   `AUTHENTIK_CLIENT_ID`, and `AUTHENTIK_CLIENT_SECRET`, then `docker compose up -d --build`.

A "Login with Authentik" link then appears on the login page. Signing in via Authentik only
works for usernames already provisioned with `scripts/create_user.py` here — Authentik proves
*who* someone is, this gateway's local user list still decides *whether* they're allowed
through and which `aw-server-<username>` they land on.
