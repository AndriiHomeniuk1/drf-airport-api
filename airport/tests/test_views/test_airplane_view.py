from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from airport.tests.factories import (
    sample_airplane,
    sample_user,
    sample_airplane_type
)


LIST_URL = reverse("airport:airplane-list")

def detail_url(airplane_id: int) -> str:
    return reverse("airport:airplane-detail", args=[airplane_id])


class AirplaneViewSetTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.airplane = sample_airplane()

    def test_list_serializer_class(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("airplane_type", res.data["results"][0])
        self.assertIsInstance(res.data["results"][0]["airplane_type"], str)

    def test_retrieve_serializer_class(self):
        res = self.client.get(detail_url(self.airplane.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("airplane_type", res.data)
        self.assertIsInstance(res.data["airplane_type"], dict)

    def test_queryset_filters_inactive_airplanes(self):
        inactive = sample_airplane(
            name="Test",
            airplane_type=sample_airplane_type(name="Test"),
            is_active=False
        )
        res = self.client.get(LIST_URL)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(self.airplane.pk, ids)
        self.assertNotIn(inactive.pk, ids)


class AirplaneViewSetAnonymousTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.airplane = sample_airplane()

    def test_list_unauthorized_for_anonymous(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized_for_anonymous(self):
        res = self.client.get(detail_url(self.airplane.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AirplaneViewSetPermissionsTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user(is_staff=False)
        self.client.force_authenticate(user=self.user)
        self.airplane = sample_airplane()

    def test_list_allowed_for_user(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_allowed_for_user(self):
        res = self.client.get(detail_url(self.airplane.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_forbidden_for_user(self):
        data = {
            "name": "New Airplane",
            "rows": 5,
            "seats_in_row": 4,
            "airplane_type": sample_airplane_type(name="TestType").pk
        }
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_forbidden_for_user(self):
        data = {"name": "Updated Name"}
        res = self.client.patch(detail_url(self.airplane.pk), data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_forbidden_for_user(self):
        res = self.client.delete(detail_url(self.airplane.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AirplaneViewSetAdminTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.airplane = sample_airplane()

    def test_create_allowed_for_admin(self):
        data = {
            "name": "Admin Airplane",
            "rows": 8,
            "seats_in_row": 4,
            "airplane_type": sample_airplane_type(name="AdminType").pk,
        }
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_allowed_for_admin(self):
        data = {"name": "Updated by Admin"}
        res = self.client.patch(detail_url(self.airplane.pk), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.airplane.refresh_from_db()
        self.assertEqual(self.airplane.name, data["name"])

    def test_delete_allowed_for_admin(self):
        res = self.client.delete(detail_url(self.airplane.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.airplane.refresh_from_db()
        self.assertFalse(self.airplane.is_active)
