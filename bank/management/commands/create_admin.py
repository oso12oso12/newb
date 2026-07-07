import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    """Creates (or updates) a single superuser from environment variables.

    Meant to run automatically on every deploy (wired into the Procfile's
    `release` step) so you get an admin account without needing interactive
    shell access, e.g. on Railway.

    Reads:
      ADMIN_USERNAME (required)
      ADMIN_EMAIL    (required)
      ADMIN_PASSWORD (required)

    Safe to run on every deploy: if the user already exists, it just makes
    sure the password/email/staff/superuser flags match the env vars
    instead of erroring out or creating a duplicate.
    """

    help = "Create or update a superuser from ADMIN_USERNAME/ADMIN_EMAIL/ADMIN_PASSWORD env vars."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")

        if not all([username, email, password]):
            self.stdout.write(
                self.style.WARNING(
                    "ADMIN_USERNAME / ADMIN_EMAIL / ADMIN_PASSWORD not all set — "
                    "skipping admin creation."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Updated existing superuser '{username}'.")
            )
