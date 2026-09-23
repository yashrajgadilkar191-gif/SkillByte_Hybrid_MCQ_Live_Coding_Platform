"""
User & Role Models for SKILLBYTE.

Architectural Decision:
To preserve Django's existing authentication tables applied during Phase 1,
we maintain a clean OneToOne UserProfile model linked to Django's standard User.
This ensures 100% backward compatibility, leverages Django's battle-tested
PBKDF2 password hashing, and cleanly separates role-management logic.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    STUDENT = 'STUDENT', _('Student')
    ADMIN = 'ADMIN', _('Admin')
    GUEST = 'GUEST', _('Guest')


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User')
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name=_('Role'),
        db_index=True
    )
    bio = models.TextField(blank=True, default='', verbose_name=_('Bio'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.user.is_superuser or self.user.is_staff

    @property
    def is_guest(self):
        return self.role == Role.GUEST

