from django.test import TestCase
from django.contrib.auth import get_user_model
from user.serializers import UserSerializer


User = get_user_model()


class UserSerializerTest(TestCase):
    def test_create_user_with_encrypted_password(self):
        data = {
            "email": "test@example.com",
            "password": "secure123",
            "first_name": "John",
            "last_name": "Doe",
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertTrue(user.check_password("secure123"))
        self.assertNotEqual(user.password, "secure123")

    def test_update_user_with_new_password(self):
        user = User.objects.create_user(
            email="update@example.com", password="oldpass")
        serializer = UserSerializer(
            user,
            data={"password": "newpass123", "first_name": "Updated"},
            partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertTrue(updated_user.check_password("newpass123"))
        self.assertEqual(updated_user.first_name, "Updated")

    def test_update_user_without_password(self):
        user = User.objects.create_user(
            email="nopass@example.com", password="secure123")
        serializer = UserSerializer(
            user, data={"first_name": "NoPass"}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertTrue(updated_user.check_password("secure123"))
        self.assertEqual(updated_user.first_name, "NoPass")

    def test_password_is_write_only(self):
        user = User.objects.create_user(
            email="writeonly@example.com", password="hidden123")
        serializer = UserSerializer(user)
        self.assertNotIn("password", serializer.data)

    def test_is_staff_is_read_only_on_create(self):
        data = {
            "email": "staff@example.com",
            "password": "secure123",
            "is_staff": True,
        }
        serializer = UserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertFalse(user.is_staff)

    def test_is_staff_is_read_only(self):
        user = User.objects.create_user(
            email="readonly@example.com", password="readonly123")
        serializer = UserSerializer(
            user, data={"is_staff": True}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_user = serializer.save()
        self.assertFalse(updated_user.is_staff)

    def test_password_min_length_validation(self):
        data = {"email": "short@example.com", "password": "123"}
        serializer = UserSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)
