#!/usr/bin/env python
"""Delete a user (revokes both local and Authentik-based access)."""

import argparse, os, sys, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gatewayproj.settings")


django.setup()

from django.contrib.auth.models import User  # noqa: E402

from proxyauth import db  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()

    db.ensure_table()
    try:
        user = User.objects.get(username=args.username)
    except User.DoesNotExist:
        print(f"No such user '{args.username}'", file=sys.stderr)
        sys.exit(1)

    db.delete_backend_host(user)
    user.delete()
    print(f"Deleted user '{args.username}'")


if __name__ == "__main__":
    main()
