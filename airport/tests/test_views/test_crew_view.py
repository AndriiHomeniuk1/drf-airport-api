from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from airport.tests.factories import sample_crew, sample_user


LIST_URL = reverse("airport:crew-list")

def detail_url(crew_id: int) -> str:
    return reverse("airport:crew-detail", args=[crew_id])


class CrewViewSetAnonymous(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.crew = sample_crew()

    def test_list_unauthorized_for_anonymous(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized_for_anonymous(self):
        res = self.client.get(detail_url(self.crew.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class CrewViewSetPermissionsTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user(is_staff=False)
        self.client.force_authenticate(user=self.user)
        self.crew = sample_crew()

    def test_list_allowed_for_user(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_allowed_for_user(self):
        res = self.client.get(detail_url(self.crew.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_forbidden_for_user(self):
        data = {"first_name": "Jane", "last_name": "Smith", "role": "pilot"}
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_forbidden_for_user(self):
        data = {"first_name": "Updated"}
        res = self.client.patch(detail_url(self.crew.pk), data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_forbidden_for_user(self):
        res = self.client.delete(detail_url(self.crew.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class CrewViewSetAdminTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.crew = sample_crew()

    def test_create_allowed_for_admin(self):
        data = {"first_name": "Admin", "last_name": "Crew", "role": "pilot"}
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_allowed_for_admin(self):
        data = {"last_name": "Updated by Admin"}
        res = self.client.patch(detail_url(self.crew.pk), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.crew.refresh_from_db()
        self.assertEqual(self.crew.last_name, data["last_name"])

    def test_destroy_allowed_for_admin(self):
        res = self.client.delete(detail_url(self.crew.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = type(self.crew).objects.filter(pk=self.crew.pk).exists()
        self.assertFalse(exists)
