from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from airport.models import Order
from airport.tests.factories import (
    sample_order,
    sample_ticket,
    sample_flight,
    sample_user
)


LIST_URL = reverse("airport:order-list")

def detail_url(order_id: int) -> str:
    return reverse("airport:order-detail", args=[order_id])


class OrderViewSetTest(APITestCase):
    def setUp(self) -> None:
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.order = sample_order(user=self.user)
        self.flight = sample_flight()
        sample_ticket(order=self.order, flight=self.flight, row=1, seat=1)

    def test_list_serializer_class(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("tickets", res.data["results"][0])
        self.assertIsInstance(res.data["results"][0]["tickets"], list)

    def test_retrieve_serializer_class(self):
        res = self.client.get(detail_url(self.order.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("tickets", res.data)
        self.assertIsInstance(res.data["tickets"], list)
        self.assertIsInstance(res.data["tickets"][0]["flight"], dict)

    def test_queryset_filters_by_user(self):
        other_user = sample_user(email="other@test.com")
        other_order = sample_order(user=other_user)
        res = self.client.get(LIST_URL)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(self.order.pk, ids)
        self.assertNotIn(other_order.pk, ids)

    def test_perform_create_sets_user(self):
        data = {
            "tickets": [
                {"row": 2, "seat": 3, "flight": self.flight.pk}
            ]
        }
        res = self.client.post(LIST_URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["tickets"][0]["row"], 2)
        self.assertEqual(res.data["tickets"][0]["seat"], 3)
        order = Order.objects.get(pk=res.data["id"])
        self.assertEqual(order.user, self.user)


class OrderViewSetAnonymousTest(APITestCase):
    def setUp(self) -> None:
        self.order = sample_order()
        self.flight = sample_flight()

    def test_list_unauthorized_for_anonymous(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthorized_for_anonymous(self):
        res = self.client.get(detail_url(self.order.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_unauthorized_for_anonymous(self):
        data = {"tickets": [{"row": 2, "seat": 3, "flight": self.flight.pk}]}
        res = self.client.post(LIST_URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_destroy_unauthorized_for_anonymous(self):
        res = self.client.delete(detail_url(self.order.pk))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderViewSetPermissionsTest(APITestCase):
    def setUp(self) -> None:
        self.user = sample_user(is_staff=False)
        self.client.force_authenticate(user=self.user)
        self.order = sample_order(user=self.user)
        self.flight = sample_flight()

    def test_list_allowed_for_user(self):
        res = self.client.get(LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_allowed_for_user(self):
        res = self.client.get(detail_url(self.order.pk))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_cannot_access_other_orders(self):
        other_user = sample_user(email="other@test.com")
        other_order = sample_order(user=other_user)
        res = self.client.get(detail_url(other_order.pk))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_allowed_for_user(self):
        data = {"tickets": [{"row": 1, "seat": 1, "flight": self.flight.pk}]}
        res = self.client.post(LIST_URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["tickets"][0]["row"], 1)

    def test_update_not_allowed_for_user(self):
        data = {"tickets": [{"row": 2, "seat": 2, "flight": self.flight.pk}]}
        res = self.client.put(detail_url(self.order.pk), data, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update_not_allowed_for_user(self):
        data = {"tickets": [{"row": 3}]}
        res = self.client.put(detail_url(self.order.pk), data, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_destroy_allowed_for_user(self):
        res = self.client.delete(detail_url(self.order.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = type(self.order).objects.filter(pk=self.order.pk).exists()
        self.assertFalse(exists)


class OrderViewSetAdminTest(APITestCase):
    def setUp(self) -> None:
        self.admin = sample_user(is_staff=True)
        self.client.force_authenticate(user=self.admin)
        self.order = sample_order(user=self.admin)
        self.flight = sample_flight()

    def test_admin_sees_only_own_orders(self):
        other_user = sample_user(email="other2@test.com")
        other_order = sample_order(user=other_user)
        res = self.client.get(LIST_URL)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(self.order.pk, ids)
        self.assertNotIn(other_order.pk, ids)

    def test_create_allowed_for_admin(self):
        data = {"tickets": [{"row": 3, "seat": 1, "flight": self.flight.pk}]}
        res = self.client.post(LIST_URL, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_update_not_allowed_for_admin(self):
        data = {"tickets": [{"row": 4, "seat": 4, "flight": self.flight.pk}]}
        res = self.client.put(detail_url(self.order.pk), data, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_partial_update_not_allowed_for_admin(self):
        data = {"tickets": [{"row": 5}]}
        res = self.client.patch(detail_url(self.order.pk), data, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_destroy_allowed_for_admin(self):
        res = self.client.delete(detail_url(self.order.pk))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        exists = type(self.order).objects.filter(pk=self.order.pk).exists()
        self.assertFalse(exists)
