#!/usr/bin/env python
"""Create or update a user allowed to sign in (with a local password and/or via
Authentik, if configured) and the aw-server backend they're routed to.
"""

import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gatewayproj.settings")

import django

django.setup()

from django.contrib.auth.models import User

from proxyauth import db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument(
        "--password", help="If omitted, prompts securely unless --no-password."
    )
    parser.add_argument(
        "--no-password",
        action="store_true",
        help="Don't set a usable local password; user can only sign in via Authentik.",
    )
    parser.add_argument(
        "--backend-host",
        help="Internal host:port of this user's aw-server "
        "(default: aw-server-<username>:5600)",
    )
    args = parser.parse_args()

    db.ensure_table()
    backend_host = args.backend_host or f"aw-server-{args.username}:5600"

    user, _created = User.objects.get_or_create(username=args.username)
    if args.no_password:
        user.set_unusable_password()
    else:
        password = args.password or getpass.getpass(f"Password for {args.username}: ")
        user.set_password(password)
    user.save()
    db.set_backend_host(user, backend_host)

    print(f"User '{args.username}' -> {backend_host}")


if __name__ == "__main__":
    main()
