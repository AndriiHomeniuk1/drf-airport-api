from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from airport.serializers import RouteSerializer, FlightSerializer
from airport.tests.test_models import (
    sample_airport,
    sample_route,
    sample_airplane,
    sample_airplane_type,
    sample_flight,
    sample_crew,
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


class FlightSerializerTest(TestCase):
    def setUp(self) -> None:
        self.route = sample_route()
        self.airplane = sample_airplane()
        self.departure = timezone.now()
        self.arrival = self.departure + timedelta(hours=2)

    def test_valid_flight_serializer(self):
        data = {
            "route": self.route.pk,
            "airplane": self.airplane.pk,
            "departure_time": self.departure,
            "arrival_time": self.arrival,
            "crew": []
        }
        serializer = FlightSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        flight = serializer.save()
        self.assertEqual(flight.route, self.route)
        self.assertEqual(flight.airplane, self.airplane)

    def test_invalid_route(self):
        inactive_route = sample_route(
            source=sample_airport(name="Kiev"),
            destination=sample_airport(name="Malmo"),
            is_active=False
        )
        data = {
            "route": inactive_route.pk,
            "airplane": self.airplane.pk,
            "departure_time": self.departure,
            "arrival_time": self.arrival,
            "crew": []
        }
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("route", serializer.errors)

    def test_invalid_airplane(self):
        inactive_airplane = sample_airplane(
            name="Inactive Airplane",
            airplane_type=sample_airplane_type(name="test"),
            is_active=False
        )
        data = {
            "route": self.route.pk,
            "airplane": inactive_airplane.pk,
            "departure_time": self.departure,
            "arrival_time": self.arrival,
            "crew": []
        }
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("airplane", serializer.errors)

    def test_invalid_time(self):
        data = {
            "route": self.route.pk,
            "airplane": self.airplane.pk,
            "departure_time": self.departure,
            "arrival_time": self.departure,
            "crew": []
        }
        serializer = FlightSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("arrival_time", serializer.errors)

    def test_serializer_representation(self):
        flight = sample_flight(route=self.route, airplane=self.airplane)
        serializer = FlightSerializer(flight)
        self.assertEqual(serializer.data["route"], self.route.pk)
        self.assertEqual(serializer.data["airplane"], self.airplane.pk)
        self.assertEqual(
            parse_datetime(serializer.data["departure_time"]),
            flight.departure_time
        )
        self.assertEqual(
            parse_datetime(serializer.data["arrival_time"]),
            flight.arrival_time
        )
