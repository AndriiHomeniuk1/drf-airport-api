from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from airport.tests.factories import sample_route, sample_airport, sample_user


LIST_URL = reverse("airport:route-list")

def detail_url(route_id: int) -> str:
    return reverse("airport:route-detail", args=[route_id])


class RouteViewSetTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.route = sample_route()

    def test_list_serializer_class(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data["results"][0]["source"], str)
        self.assertIsInstance(res.data["results"][0]["destination"], str)

    def test_retrieve_serializer_class(self):
        res = self.client.get(detail_url(self.route.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data["source"], dict)
        self.assertIsInstance(res.data["destination"], dict)

    def test_queryset_filters_inactive_routes(self):
        inactive = sample_route(
            source=sample_airport(name="Inactive Source"),
            destination=sample_airport(name="Inactive Destination"),
            is_active=False
        )
        res = self.client.get(LIST_URL)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(self.route.pk, ids)
        self.assertNotIn(inactive.pk, ids)


class RouteViewSetAnonymousTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.route = sample_route()

    def test_list_unauthorized_for_anonymous(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized_for_anonymous(self):
        res = self.client.get(detail_url(self.route.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class RouteViewSetPermissionsTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = sample_user(is_staff=False)
        self.client.force_authenticate(user=self.user)
        self.route = sample_route()

    def test_list_allowed_for_user(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_allowed_for_user(self):
        res = self.client.get(detail_url(self.route.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_forbidden_for_user(self):
        data = {
            "source": sample_airport(name="Source").pk,
            "destination": sample_airport(name="destination").pk,
            "distance": 150
        }
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_forbidden_for_user(self):
        data = {"distance": 200}
        res = self.client.patch(detail_url(self.route.pk), data)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_forbidden_for_user(self):
        res = self.client.delete(detail_url(self.route.pk))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class RouteViewSetAdminTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.admin = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.route = sample_route()

    def test_create_allowed_for_admin(self):
        data = {
            "source": sample_airport(name="Admin Source").pk,
            "destination": sample_airport(name="Admin Destination").pk,
            "distance": 300
        }
        res = self.client.post(LIST_URL, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_allowed_for_admin(self):
        data = {"distance": 400}
        res = self.client.patch(detail_url(self.route.pk), data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.route.refresh_from_db()
        self.assertEqual(self.route.distance, 400)

    def test_destroy_allowed_for_admin(self):
        res = self.client.delete(detail_url(self.route.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.route.refresh_from_db()
        self.assertFalse(self.route.is_active)
