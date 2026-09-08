from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError


User = get_user_model()


class UserManagerTest(TestCase):
    def test_create_user_success(self):
        user = User.objects.create_user(
            email="test@test.com", password="pass123")
        self.assertEqual(user.email, "test@test.com")
        self.assertTrue(user.check_password("pass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_success(self):
        admin = User.objects.create_superuser(
            email="admin@test.com", password="admin123")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_invalid_flags(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="bad@test.com", password="bad123", is_staff=False)
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="bad2@test.com", password="bad123", is_superuser=False)

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass123")

    def test_email_is_normalized(self):
        email = "TestUser@Example.COM"
        user = User.objects.create_user(
            email=email,password="test12345")
        self.assertEqual(user.email, "TestUser@example.com")


class UserModelTest(TestCase):
    def test_email_is_unique(self):
        User.objects.create_user(email="unique@test.com", password="pass123")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="unique@test.com", password="pass456")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertIsNone(User.username)

    def test_required_fields_empty(self):
        self.assertEqual(User.REQUIRED_FIELDS, [])

    def test_str_returns_email(self):
        user = User.objects.create_user(
            email="str@test.com", password="pass123")
        self.assertEqual(str(user), "str@test.com")
