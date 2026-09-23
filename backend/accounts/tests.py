"""
Automated Test Suite for SKILLBYTE Authentication & User Roles (Phase 2).
"""

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import UserProfile, Role


class AuthenticationTests(APITestCase):
    """
    Comprehensive tests for Student Registration, Login, JWT, Roles, and Permissions.
    """

    def setUp(self):
        # Endpoints
        self.register_url = reverse('auth_register')
        self.login_url = reverse('auth_login')
        self.refresh_url = reverse('auth_refresh')
        self.logout_url = reverse('auth_logout')
        self.me_url = reverse('auth_me')
        self.student_role_url = reverse('test_student_role')
        self.admin_role_url = reverse('test_admin_role')

        # Base valid student payload
        self.valid_student_data = {
            "name": "Alex Mercer",
            "email": "alex@skillbyte.edu",
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123"
        }

    # 1. Successful student registration
    def test_01_successful_student_registration(self):
        response = self.client.post(self.register_url, self.valid_student_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "alex@skillbyte.edu")
        self.assertEqual(response.data["user"]["role"], Role.STUDENT)
        self.assertTrue(User.objects.filter(email="alex@skillbyte.edu").exists())

    # 2. Duplicate email registration
    def test_02_duplicate_email_registration(self):
        self.client.post(self.register_url, self.valid_student_data, format='json')
        duplicate_data = self.valid_student_data.copy()
        duplicate_data["name"] = "Different Name"
        response = self.client.post(self.register_url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    # 3. Invalid email registration
    def test_03_invalid_email_registration(self):
        invalid_data = self.valid_student_data.copy()
        invalid_data["email"] = "not-a-valid-email"
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    # 4. Short password
    def test_04_short_password(self):
        short_pw_data = self.valid_student_data.copy()
        short_pw_data["password"] = "short"
        short_pw_data["confirm_password"] = "short"
        response = self.client.post(self.register_url, short_pw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    # 5. Password mismatch
    def test_05_password_mismatch(self):
        mismatch_data = self.valid_student_data.copy()
        mismatch_data["confirm_password"] = "DifferentPassword123"
        response = self.client.post(self.register_url, mismatch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)

    # 6. Admin role injection attempt
    def test_06_admin_role_injection_rejected(self):
        tampered_data = self.valid_student_data.copy()
        tampered_data["role"] = "ADMIN"
        response = self.client.post(self.register_url, tampered_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)

    # 7. Successful login
    def test_07_successful_login(self):
        self.client.post(self.register_url, self.valid_student_data, format='json')
        login_payload = {
            "email": "alex@skillbyte.edu",
            "password": "SecurePassword123"
        }
        response = self.client.post(self.login_url, login_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "alex@skillbyte.edu")
        self.assertEqual(response.data["user"]["role"], Role.STUDENT)

    # 8. Invalid login
    def test_08_invalid_login(self):
        self.client.post(self.register_url, self.valid_student_data, format='json')
        # Wrong password
        response = self.client.post(self.login_url, {
            "email": "alex@skillbyte.edu",
            "password": "WrongPassword999"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Nonexistent email
        response = self.client.post(self.login_url, {
            "email": "ghost@skillbyte.edu",
            "password": "SecurePassword123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 9. JWT refresh
    def test_09_jwt_refresh(self):
        self.client.post(self.register_url, self.valid_student_data, format='json')
        login_res = self.client.post(self.login_url, {
            "email": "alex@skillbyte.edu",
            "password": "SecurePassword123"
        }, format='json')
        refresh_token = login_res.data["refresh"]

        refresh_res = self.client.post(self.refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_res.data)

    # 10. GET /api/auth/me/ with valid JWT
    def test_10_get_me_with_valid_jwt(self):
        self.client.post(self.register_url, self.valid_student_data, format='json')
        login_res = self.client.post(self.login_url, {
            "email": "alex@skillbyte.edu",
            "password": "SecurePassword123"
        }, format='json')
        access_token = login_res.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_res = self.client.get(self.me_url)
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data["email"], "alex@skillbyte.edu")
        self.assertEqual(me_res.data["role"], Role.STUDENT)

    # 11. GET /api/auth/me/ without JWT
    def test_11_get_me_without_jwt_returns_401(self):
        self.client.credentials()  # clear auth header
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 12. Student permission check
    def test_12_student_permission_check(self):
        self.client.post(self.register_url, self.valid_student_data, format='json')
        login_res = self.client.post(self.login_url, {
            "email": "alex@skillbyte.edu",
            "password": "SecurePassword123"
        }, format='json')
        access_token = login_res.data["access"]

        # Student accesses student endpoint -> 200 OK
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        res = self.client.get(self.student_role_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Unauthenticated accesses student endpoint -> 401
        self.client.credentials()
        res_unauth = self.client.get(self.student_role_url)
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

    # 13. Admin permission check
    def test_13_admin_permission_check(self):
        # Register a student
        self.client.post(self.register_url, self.valid_student_data, format='json')
        student_login = self.client.post(self.login_url, {
            "email": "alex@skillbyte.edu",
            "password": "SecurePassword123"
        }, format='json')
        student_token = student_login.data["access"]

        # Student tries to access admin endpoint -> 403 Forbidden
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {student_token}")
        forbidden_res = self.client.get(self.admin_role_url)
        self.assertEqual(forbidden_res.status_code, status.HTTP_403_FORBIDDEN)

        # Create an admin user programmatically
        admin_user = User.objects.create_superuser(
            username="sysadmin",
            email="admin@skillbyte.edu",
            password="AdminSuperSecret123"
        )
        admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        admin_profile.role = Role.ADMIN
        admin_profile.save()

        # Admin logs in
        admin_login = self.client.post(self.login_url, {
            "email": "admin@skillbyte.edu",
            "password": "AdminSuperSecret123"
        }, format='json')
        admin_token = admin_login.data["access"]

        # Admin accesses admin endpoint -> 200 OK
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
        admin_res = self.client.get(self.admin_role_url)
        self.assertEqual(admin_res.status_code, status.HTTP_200_OK)

    # 14. Logout & token invalidation
    def test_14_logout_invalidates_refresh_token(self):
        self.client.post(self.register_url, self.valid_student_data, format='json')
        login_res = self.client.post(self.login_url, {
            "email": "alex@skillbyte.edu",
            "password": "SecurePassword123"
        }, format='json')
        access_token = login_res.data["access"]
        refresh_token = login_res.data["refresh"]

        # Logout with refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_res = self.client.post(self.logout_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Attempt to refresh with the blacklisted token -> 401 Unauthorized
        second_refresh_res = self.client.post(self.refresh_url, {"refresh": refresh_token}, format='json')
        self.assertEqual(second_refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)

