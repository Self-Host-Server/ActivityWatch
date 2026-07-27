import argparse
import getpass
import sys

from . import db
from .auth import hash_password


def cmd_create_user(args: argparse.Namespace) -> None:
    password = args.password or getpass.getpass(f"Password for {args.username}: ")
    backend_host = args.backend_host or f"aw-server-{args.username}:5600"
    db.upsert_user(args.username, hash_password(password), backend_host)
    print(f"User '{args.username}' -> {backend_host}")


def cmd_delete_user(args: argparse.Namespace) -> None:
    if db.delete_user(args.username):
        print(f"Deleted user '{args.username}'")
    else:
        print(f"No such user '{args.username}'", file=sys.stderr)
        sys.exit(1)


def cmd_list_users(_args: argparse.Namespace) -> None:
    users = db.list_users()
    if not users:
        print("No users configured")
        return
    for user in users:
        print(f"{user['username']} -> {user['backend_host']}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="gateway-users")
    sub = parser.add_subparsers(required=True)

    p_create = sub.add_parser("create-user", help="Create or update a user")
    p_create.add_argument("username")
    p_create.add_argument("--password", help="If omitted, prompts securely")
    p_create.add_argument(
        "--backend-host",
        help="Internal host:port of this user's aw-server (default: aw-server-<username>:5600)",
    )
    p_create.set_defaults(func=cmd_create_user)

    p_delete = sub.add_parser("delete-user", help="Delete a user")
    p_delete.add_argument("username")
    p_delete.set_defaults(func=cmd_delete_user)

    p_list = sub.add_parser("list-users", help="List configured users")
    p_list.set_defaults(func=cmd_list_users)

    args = parser.parse_args()
    db.init_db()
    args.func(args)


if __name__ == "__main__":
    main()
