"""Which aw-server instance each provisioned user is routed to.

Deliberately raw SQL instead of a Django ORM model: this repo's no-classes-check
(scripts/no_classes_check.py) rejects any class definition, and Django's ORM has
no functional way to declare a model without one. Existence of a row here (not
just a Django auth User row) is what grants access to the proxy — see
proxyauth.views.proxy_view.
"""

from django.contrib.auth.models import User
from django.db import connection


def ensure_table():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS proxyauth_backend_mapping (
                user_id INTEGER PRIMARY KEY REFERENCES auth_user(id) ON DELETE CASCADE,
                backend_host TEXT NOT NULL
            )
            """
        )


def get_backend_host(username: str) -> str | None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT m.backend_host
            FROM proxyauth_backend_mapping m
            JOIN auth_user u ON u.id = m.user_id
            WHERE u.username = %s
            """,
            [username],
        )
        row = cursor.fetchone()
        return row[0] if row else None


def set_backend_host(user: User, backend_host: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO proxyauth_backend_mapping (user_id, backend_host) VALUES (%s, %s)
            ON CONFLICT(user_id) DO UPDATE SET backend_host = excluded.backend_host
            """,
            [user.id, backend_host],
        )


def delete_backend_host(user: User) -> None:
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM proxyauth_backend_mapping WHERE user_id = %s", [user.id])


def list_mappings() -> list[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.username, m.backend_host
            FROM proxyauth_backend_mapping m
            JOIN auth_user u ON u.id = m.user_id
            ORDER BY u.username
            """
        )
        return cursor.fetchall()
