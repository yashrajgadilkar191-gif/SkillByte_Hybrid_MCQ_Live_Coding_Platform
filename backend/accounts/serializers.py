"""
Serializers for SKILLBYTE Authentication & User Profile.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .models import UserProfile, Role


class UserSerializer(serializers.ModelSerializer):
    """
    Public representation of a SkillByte user. Never exposes sensitive fields.
    """
    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'role']
        read_only_fields = ['id', 'name', 'email', 'role']

    def get_name(self, obj):
        return obj.first_name.strip() or obj.username

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return Role.STUDENT


class RegisterSerializer(serializers.Serializer):
    """
    Student registration serializer.
    Strictly forbids and rejects/ignores client attempts to assign the ADMIN role.
    """
    name = serializers.CharField(required=True, max_length=150, trim_whitespace=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=8, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    role = serializers.CharField(required=False, write_only=True)

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Name is required.")
        return value.strip()

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return normalized_email

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        # Explicitly enforce STUDENT role; public registration NEVER creates ADMIN
        if attrs.get('role') and attrs.get('role').upper() == 'ADMIN':
            # Ignore or reject: per requirements, explicitly reject or prevent ADMIN
            raise serializers.ValidationError({"role": "Public registration for the ADMIN role is strictly forbidden."})

        return attrs

    def create(self, validated_data):
        name = validated_data['name']
        email = validated_data['email']
        password = validated_data['password']

        # Generate unique username from email
        username = email
        base_username = email.split('@')[0]
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        user = User(
            username=username,
            email=email,
            first_name=name,
            is_active=True
        )
        user.set_password(password)
        user.save()

        # Enforce STUDENT role in profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = Role.STUDENT
        profile.save()

        return user


class LoginSerializer(serializers.Serializer):
    """
    Email-based login serializer that returns JWT access & refresh tokens.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is inactive or disabled.")

        refresh = RefreshToken.for_user(user)

        # Include custom claims
        refresh['role'] = getattr(user.profile, 'role', Role.STUDENT) if hasattr(user, 'profile') else Role.STUDENT
        refresh['email'] = user.email
        refresh['name'] = user.first_name.strip() or user.username

        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class LogoutSerializer(serializers.Serializer):
    """
    Handles JWT invalidation by adding the refresh token to the blacklist.
    """
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError as e:
            raise serializers.ValidationError({'refresh': f"Invalid or expired token: {str(e)}"})

