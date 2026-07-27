import getpass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from proxyauth.models import BackendMapping


class Command(BaseCommand):
    help = (
        "Create or update a user allowed to sign in (with a local password and/or "
        "via Authentik, if configured) and the aw-server backend they're routed to."
    )

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        username = options["username"]
        backend_host = options["backend_host"] or f"aw-server-{username}:5600"

        with transaction.atomic():
            user, _ = User.objects.get_or_create(username=username)
            if options["no_password"]:
                user.set_unusable_password()
            else:
                password = options["password"] or getpass.getpass(
                    f"Password for {username}: "
                )
                user.set_password(password)
            user.save()
            BackendMapping.objects.update_or_create(
                user=user, defaults={"backend_host": backend_host}
            )

        self.stdout.write(self.style.SUCCESS(f"User '{username}' -> {backend_host}"))
