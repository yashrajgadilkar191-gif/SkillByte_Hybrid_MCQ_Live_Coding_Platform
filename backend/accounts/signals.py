"""
Signals for UserProfile lifecycle management.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Role


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """
    Automatically creates a UserProfile for every new User,
    and updates existing ones.
    """
    if created:
        # If user is superuser, default role to ADMIN, else STUDENT
        default_role = Role.ADMIN if instance.is_superuser else Role.STUDENT
        UserProfile.objects.get_or_create(user=instance, defaults={'role': default_role})
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            default_role = Role.ADMIN if instance.is_superuser else Role.STUDENT
            UserProfile.objects.create(user=instance, role=default_role)

