from django.core.management.base import BaseCommand

from proxyauth.models import BackendMapping


class Command(BaseCommand):
    help = "List provisioned users and the aw-server backend each is routed to"

    def handle(self, *args, **options):
        mappings = BackendMapping.objects.select_related("user").all()
        if not mappings:
            self.stdout.write("No users configured")
            return
        for mapping in mappings:
            self.stdout.write(f"{mapping.user.username} -> {mapping.backend_host}")
