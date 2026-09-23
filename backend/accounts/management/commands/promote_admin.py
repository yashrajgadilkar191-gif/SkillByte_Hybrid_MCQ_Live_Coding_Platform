"""
Management command to promote an existing user to Administrator.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.models import UserProfile, Role


class Command(BaseCommand):
    help = 'Promote an existing user to Administrator role.'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email of user to promote')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise CommandError(f"No user found with email '{email}'.")
        except User.MultipleObjectsReturned:
            raise CommandError(f"Multiple users found with email '{email}'.")

        user.is_staff = True
        user.is_superuser = True
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = Role.ADMIN
        profile.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully promoted user '{user.username}' ({user.email}) to role ADMIN with superuser privileges."))

