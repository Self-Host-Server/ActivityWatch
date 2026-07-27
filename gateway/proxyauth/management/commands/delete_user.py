from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Delete a user (revokes both local and Authentik-based access)"

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        deleted, _ = User.objects.filter(username=username).delete()
        if deleted:
            self.stdout.write(self.style.SUCCESS(f"Deleted user '{username}'"))
        else:
            raise CommandError(f"No such user '{username}'")
