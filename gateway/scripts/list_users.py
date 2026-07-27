#!/usr/bin/env python
"""List provisioned users and the aw-server backend each is routed to."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gatewayproj.settings")

import django

django.setup()

from proxyauth import db


def main():
    db.ensure_table()
    mappings = db.list_mappings()
    if not mappings:
        print("No users configured")
        return
    for username, backend_host in mappings:
        print(f"{username} -> {backend_host}")


if __name__ == "__main__":
    main()
