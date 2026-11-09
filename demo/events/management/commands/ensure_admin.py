from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create (or reset) the demo superuser: admin / admin."

    def handle(self, *args, **options):
        user, created = get_user_model().objects.get_or_create(username="admin")
        user.is_staff = user.is_superuser = True
        user.set_password("admin")
        user.save()
        self.stdout.write(
            f"{'Created' if created else 'Reset'} superuser admin (password: admin)"
        )
