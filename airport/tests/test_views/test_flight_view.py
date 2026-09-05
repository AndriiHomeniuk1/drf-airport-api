from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from airport.tests.factories import (
    sample_flight,
    sample_airplane_type,
    sample_airplane,
    sample_user,
    sample_crew
)

LIST_URL = reverse("airport:flight-list")

def detail_url(flight_id: int) -> str:
    return reverse("airport:flight-detail", args=[flight_id])


class FlightViewSetTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.flight = sample_flight()

    def test_list_serializer_class(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data["results"][0]["route"], str)
        self.assertIsInstance(res.data["results"][0]["airplane"], str)

    def test_retrieve_serializer_class(self):
        res = self.client.get(detail_url(self.flight.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data["route"], dict)
        self.assertIsInstance(res.data["airplane"], dict)
        self.assertIsInstance(res.data["crew"], list)

    def test_queryset_list_select_related(self):
        with self.assertNumQueries(2):
            self.client.get(LIST_URL)

    def test_queryset_retrieve_prefetch_related(self):
        crew = sample_crew()
        self.flight.crew.add(crew)
        with self.assertNumQueries(2):
            self.client.get(detail_url(self.flight.pk))


class FlightViewSetAnonymousTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.flight = sample_flight()

    def test_list_unauthorized_for_anonymous(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized_for_anonymous(self):
        res = self.client.get(detail_url(self.flight.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class FlightViewSetPermissionsTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user(is_staff=False)
        self.client.force_authenticate(user=self.user)
        self.flight = sample_flight()

    def test_list_allowed_for_user(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_allowed_for_user(self):
        res = self.client.get(detail_url(self.flight.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_forbidden_for_user(self):
        data = {
            "route": self.flight.route.pk,
            "airplane": sample_airplane(
                name="airplane user",
                airplane_type=sample_airplane_type(name="airplane type user")
            ).pk,
            "departure_time": self.flight.departure_time,
            "arrival_time": self.flight.arrival_time,
        }
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_forbidden_for_user(self):
        data = {"arrival_time": self.flight.arrival_time}
        res = self.client.patch(detail_url(self.flight.pk), data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_forbidden_for_user(self):
        res = self.client.delete(detail_url(self.flight.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class FlightViewSetAdminTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.flight = sample_flight()

    def test_create_allowed_for_admin(self):
        data = {
            "route": self.flight.route.pk,
            "airplane": sample_airplane(
                name="airplane admin",
                airplane_type=sample_airplane_type(name="airplane type admin")
            ).pk,
            "departure_time": self.flight.departure_time,
            "arrival_time": self.flight.arrival_time,
        }
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_allowed_for_admin(self):
        new_arrival = self.flight.arrival_time
        data = {"arrival_time": new_arrival}
        res = self.client.patch(detail_url(self.flight.pk), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_allowed_for_admin(self):
        res = self.client.delete(detail_url(self.flight.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = type(self.flight).objects.filter(pk=self.flight.pk).exists()
        self.assertFalse(exists)
