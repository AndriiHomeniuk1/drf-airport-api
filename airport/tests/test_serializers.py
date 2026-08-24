from django.test import TestCase

from airport.serializers import RouteSerializer
from airport.tests.test_models import (
    sample_airport,
    sample_route,
)


class RouteSerializerTest(TestCase):
    def setUp(self) -> None:
        self.source = sample_airport(name="Source Airport", is_active=True)
        self.destination = sample_airport(
            name="Destination Airport", is_active=True)

    def test_valid_route_serializer(self):
        data = {
            "source": self.source.pk,
            "destination": self.destination.pk,
            "distance": 120
        }
        serializer = RouteSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        route = serializer.save()
        self.assertEqual(route.source, self.source)
        self.assertEqual(route.destination, self.destination)

    def test_invalid_source_airport(self):
        inactive_source = sample_airport(
            name="Inactive Source", is_active=False)

        data = {
            "source": inactive_source.pk,
            "destination": self.destination.pk,
            "distance": 120
        }
        serializer = RouteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("source", serializer.errors)

    def test_invalid_destination_airport(self):
        inactive_destination = sample_airport(
            name="Inactive Destination", is_active=False)

        data = {
            "source": self.source.pk,
            "destination": inactive_destination.pk,
            "distance": 120
        }
        serializer = RouteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("destination", serializer.errors)

    def test_serializer_representation(self):
        route = sample_route(
            source=self.source, destination=self.destination, distance=150)
        serializer = RouteSerializer(route)
        self.assertEqual(serializer.data["source"], self.source.pk)
        self.assertEqual(serializer.data["destination"], self.destination.pk)
        self.assertEqual(serializer.data["distance"], 150)
