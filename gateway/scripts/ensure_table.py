#!/usr/bin/env python
"""Create proxyauth's backend-mapping table if it doesn't exist yet. Run at
container startup, since there's no Django ORM model/migration for it."""

import os, sys, django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gatewayproj.settings")


django.setup()

from proxyauth import db  # noqa: E402

if __name__ == "__main__":
    db.ensure_table()
