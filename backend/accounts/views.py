"""
Views for SKILLBYTE Authentication & User Management.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsStudent, IsAdmin


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Registers a new student. Enforces STUDENT role.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'auth_attempt'

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Registration successful. You can now login.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Authenticates student/admin with email and password, returning JWT tokens.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'auth_attempt'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response({
                "access": serializer.validated_data['access'],
                "refresh": serializer.validated_data['refresh'],
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """
    GET /api/auth/me/
    Returns currently authenticated user profile.
    PUT / PATCH /api/auth/me/
    Updates user personal details (first name, last name, email).
    Requires Bearer token; unauthenticated returns HTTP 401.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Verifies current password and securely updates to new password.
    Requires Bearer token; unauthenticated returns HTTP 401.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Password has been successfully updated."
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the provided refresh token to invalidate JWT session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentRoleTestView(APIView):
    """
    GET /api/auth/test-student-role/
    Protected endpoint to test student permission.
    """
    permission_classes = [IsStudent]

    def get(self, request):
        return Response({
            "status": "ok",
            "message": "Student permission granted.",
            "user": request.user.username,
            "role": request.user.profile.role
        }, status=status.HTTP_200_OK)


class AdminRoleTestView(APIView):
    """
    GET /api/auth/test-admin-role/
    Protected endpoint to test admin permission.
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({
            "status": "ok",
            "message": "Administrator permission granted.",
            "user": request.user.username,
            "role": request.user.profile.role
        }, status=status.HTTP_200_OK)

