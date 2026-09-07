from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from airport.tests.factories import (
    sample_airplane_type,
    sample_user
)

LIST_URL = reverse("airport:airplanetype-list")

def detail_url(type_id: int) -> str:
    return reverse("airport:airplanetype-detail", args=[type_id])


class AirplaneTypeViewSetAnonymousTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.airplane_type = sample_airplane_type()

    def test_list_unauthorized_for_anonymous(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized_for_anonymous(self):
        res = self.client.get(detail_url(self.airplane_type.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AirplaneTypeViewSetPermissionsTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user(is_staff=False)
        self.client.force_authenticate(user=self.user)
        self.airplane_type = sample_airplane_type()

    def test_list_allowed_for_user(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_allowed_for_user(self):
        res = self.client.get(detail_url(self.airplane_type.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_forbidden_for_user(self):
        data = {"name": "UserType"}
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_forbidden_for_user(self):
        data = {"name": "UpdatedType"}
        res = self.client.put(detail_url(self.airplane_type.pk), data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_forbidden_for_user(self):
        res = self.client.delete(detail_url(self.airplane_type.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AirplaneTypeViewSetAdminTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.airplane_type = sample_airplane_type()

    def test_create_allowed_for_admin(self):
        data = {"name": "AdminType"}
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_allowed_for_admin(self):
        data = {"name": "UpdatedByAdmin"}
        res = self.client.put(detail_url(self.airplane_type.pk), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.airplane_type.refresh_from_db()
        self.assertEqual(self.airplane_type.name, "UpdatedByAdmin")

    def test_destroy_allowed_for_admin(self):
        res = self.client.delete(detail_url(self.airplane_type.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = (
            type(self.airplane_type)
            .objects.filter(pk=self.airplane_type.pk).exists()
        )
        self.assertFalse(exists)
