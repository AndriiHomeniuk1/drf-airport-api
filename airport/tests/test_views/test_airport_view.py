from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from airport.tests.factories import sample_airport, sample_user


LIST_URL = reverse("airport:airport-list")

def detail_url(airport_id: int) -> str:
    return reverse("airport:airport-detail", args=[airport_id])


class AirportViewSetTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.airport = sample_airport()

    def test_queryset_filters_inactive_airports(self):
        inactive = sample_airport(name="Inactive Airport", is_active=False)
        res = self.client.get(LIST_URL)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(self.airport.pk, ids)
        self.assertNotIn(inactive.pk, ids)


class AirportViewSetAnonymousTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.airport = sample_airport()

    def test_list_unauthorized_for_anonymous(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized_for_anonymous(self):
        res = self.client.get(detail_url(self.airport.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AirportViewSetPermissionsTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user(is_staff=False)
        self.client.force_authenticate(user=self.user)
        self.airport = sample_airport()

    def test_list_allowed_for_user(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_allowed_for_user(self):
        res = self.client.get(detail_url(self.airport.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_forbidden_for_user(self):
        data = {"name": "New Airport", "closest_big_city": "Kyiv"}
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_forbidden_for_user(self):
        data = {"name": "Updated Airport"}
        res = self.client.patch(detail_url(self.airport.pk), data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_forbidden_for_user(self):
        res = self.client.delete(detail_url(self.airport.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AirportViewSetAdminTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.airport = sample_airport()

    def test_create_allowed_for_admin(self):
        data = {"name": "Admin Airport", "closest_big_city": "Helsingborg"}
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_allowed_for_admin(self):
        data = {"name": "Updated by Admin"}
        res = self.client.patch(detail_url(self.airport.pk), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.airport.refresh_from_db()
        self.assertEqual(self.airport.name, data["name"])

    def test_destroy_allowed_for_admin(self):
        res = self.client.delete(detail_url(self.airport.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.airport.refresh_from_db()
        self.assertFalse(self.airport.is_active)
