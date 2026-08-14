"""
Creates a new admin account, or promotes an existing account to admin.

Usage (run from the project root, with the virtual environment active):

    python create_admin.py

You'll be prompted for an email. If that email already has an account,
it's promoted to admin. If not, you'll be asked for a name and password
and a brand new admin account is created.
"""

import getpass
import sys

from app.database import SessionLocal
from app.models.user import User
from app.utils.security import hash_password


def main():
    db = SessionLocal()

    try:
        email = input("Email: ").strip().lower()

        if not email:
            print("An email is required.")
            sys.exit(1)

        existing = db.query(User).filter(User.email == email).first()

        if existing:
            if existing.role == "admin":
                print(f"'{email}' is already an admin. Nothing to do.")
                return

            confirm = input(
                f"An account for '{email}' already exists as '{existing.role}'. "
                f"Promote it to admin? [y/N]: "
            ).strip().lower()

            if confirm != "y":
                print("Cancelled.")
                return

            existing.role = "admin"
            db.commit()
            print(f"'{email}' is now an admin.")
            return

        print(f"No account exists yet for '{email}' — creating a new admin account.")
        name = input("Full name: ").strip()

        if not name:
            print("A name is required.")
            sys.exit(1)

        username = input("Username: ").strip()

        if not username:
            print("A username is required.")
            sys.exit(1)

        password = getpass.getpass("Password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            print("Passwords did not match.")
            sys.exit(1)

        if not password:
            print("A password is required.")
            sys.exit(1)

        user = User(
            name=name,
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="admin",
        )

        db.add(user)
        db.commit()
        print(f"Admin account created for '{email}'.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
