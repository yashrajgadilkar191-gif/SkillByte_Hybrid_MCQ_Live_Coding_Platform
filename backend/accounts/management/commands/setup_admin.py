"""
Management command to securely setup an administrator account.
Can be run interactively or non-interactively via flags.
Credentials are NEVER hardcoded.
"""

import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from accounts.models import UserProfile, Role


class Command(BaseCommand):
    help = 'Securely create or update a SkillByte Administrator account.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Admin username')
        parser.add_argument('--email', type=str, help='Admin email address')
        parser.add_argument('--name', type=str, help='Admin full name')
        parser.add_argument('--password', type=str, help='Admin password (optional flag; prompted if omitted)')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== SKILLBYTE Secure Administrator Setup ==="))

        username = options.get('username')
        email = options.get('email')
        name = options.get('name')
        password = options.get('password')

        # Interactive prompts if arguments omitted
        if not username:
            username = input("Enter admin username: ").strip()
        if not username:
            raise CommandError("Username cannot be empty.")

        if not email:
            email = input("Enter admin email: ").strip()
        try:
            validate_email(email)
        except ValidationError:
            raise CommandError(f"'{email}' is not a valid email address.")

        if not name:
            name = input("Enter admin full name [Administrator]: ").strip() or "Administrator"

        if not password:
            password = getpass.getpass("Enter admin password: ")
            confirm = getpass.getpass("Confirm admin password: ")
            if password != confirm:
                raise CommandError("Passwords do not match.")

        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters long.")

        # Create or update user
        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.first_name = name
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        # Enforce ADMIN role on profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = Role.ADMIN
        profile.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"Successfully {action} Administrator account: {username} ({email}) with role ADMIN."))

