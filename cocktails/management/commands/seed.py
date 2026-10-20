from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        admin.set_password("admin12345")
        admin.save()
        user, _ = User.objects.get_or_create(username="user", defaults={"email": "user@example.com"})
        user.set_password("user12345")
        user.save()
        self.stdout.write(self.style.SUCCESS("Konta: admin/admin12345, user/user12345"))
