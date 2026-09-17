from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()

CREATE_URL = reverse("user:create")
MANAGE_URL = reverse("user:manage_user")


class CreateUserViewTest(APITestCase):
    def test_create_user_success(self):
        data = {"email": "new@example.com", "password": "secure123"}
        res = self.client.post(CREATE_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=data["email"])
        self.assertTrue(user.check_password(data["password"]))
        self.assertNotIn("password", res.data)

    def test_create_user_password_too_short(self):
        data = {"email": "short@example.com", "password": "123"}
        res = self.client.post(CREATE_URL, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_is_staff_ignored(self):
        data = {
            "email": "staff@example.com",
            "password": "secure123",
            "is_staff": True
        }
        res = self.client.post(CREATE_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=data["email"])
        self.assertFalse(user.is_staff)


class ManageUserViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="manage@example.com", password="testpass")
        self.client.force_authenticate(user=self.user)

    def test_retrieve_user_profile(self):
        res = self.client.get(MANAGE_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)

    def test_update_user_profile(self):
        data = {"first_name": "Updated"}
        res = self.client.patch(MANAGE_URL, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    def test_update_user_password(self):
        data = {"password": "newpass123"}
        res = self.client.patch(MANAGE_URL, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

    def test_is_staff_not_updated(self):
        data = {"is_staff": True}
        res = self.client.patch(MANAGE_URL, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)


class ManageUserViewAnonymousTest(APITestCase):
    def test_retrieve_unauthorized(self):
        res = self.client.get(MANAGE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_unauthorized(self):
        res = self.client.patch(MANAGE_URL, {"first_name": "Anon"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
