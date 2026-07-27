from django.conf import settings
from django.db import models


class BackendMapping(models.Model):
    """Which aw-server instance a provisioned user is routed to.

    Existence of this row (not just a User row) is what grants access to the
    proxy — see proxyauth.views.proxy_view.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="backend"
    )
    backend_host = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} -> {self.backend_host}"
