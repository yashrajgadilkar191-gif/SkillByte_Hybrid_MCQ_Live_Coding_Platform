"""
Custom Authentication Backend for Email-based Login.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate against settings.AUTH_USER_MODEL using email or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Email can be passed via username argument or email argument
        identifier = username or kwargs.get('email')
        if not identifier or not password:
            return None

        try:
            # Match either case-insensitive email or case-insensitive username
            user = User.objects.get(Q(email__iexact=identifier) | Q(username__iexact=identifier))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

