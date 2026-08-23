from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from airport.models import (
    AirplaneType,
    Airplane,
    Airport,
    Route,
    Crew,
    Flight,
    Ticket,
    Order,
)


User = get_user_model()

def sample_airplane_type(**params):
    defaults = {
        "name": "Boeing 747",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(airplane_type=None, **params):
    if airplane_type is None:
        airplane_type = sample_airplane_type()

    defaults = {
        "name": "Test Airplane",
        "rows": 10,
        "seats_in_row": 6,
        "airplane_type": airplane_type,
        "is_active": True,
    }
    defaults.update(params)
    return Airplane.objects.create(**defaults)


def sample_airport(**params):
    defaults = {
        "name": "Lviv Airport",
        "closest_big_city": "Lviv",
        "is_active": True,
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


def sample_route(source=None, destination=None, **params):
    if source is None:
        source = sample_airport(name="Source Airport")
    if destination is None:
        destination = sample_airport(name="Destination Airport")

    defaults = {
        "source": source,
        "destination": destination,
        "distance": 100,
        "is_active": True,
    }
    defaults.update(params)
    return Route.objects.create(**defaults)


def sample_crew(**params):
    defaults = {
        "first_name": "John",
        "last_name": "Doe",
        "role": "pilot",
    }
    defaults.update(params)
    return Crew.objects.create(**defaults)


def sample_flight(route=None, airplane=None, crew=None, **params):
    if route is None:
        route = sample_route()
    if airplane is None:
        airplane = sample_airplane()

    departure = timezone.now()
    arrival = departure + timedelta(hours=2)
    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": departure,
        "arrival_time": arrival,
    }
    defaults.update(params)
    flight = Flight.objects.create(**defaults)
    if crew:
        flight.crew.set(crew)
    return flight


def sample_user(**params):
    defaults = {
        "email": "testuser@test.com",
        "password": "testpass123"
    }
    defaults.update(params)
    return User.objects.create_user(**defaults)


def sample_order(user=None, **params):
    if user is None:
        user = sample_user()
    return Order.objects.create(user=user, **params)


def sample_ticket(flight=None, order=None, **params):
    if flight is None:
        flight = sample_flight()
    if order is None:
        order = sample_order()

    defaults = {
        "row": 1,
        "seat": 1,
        "flight": flight,
        "order": order,
    }
    defaults.update(params)
    return Ticket.objects.create(**defaults)


class AirplaneTypeModelTest(TestCase):
    def setUp(self):
        self.airplane_type = sample_airplane_type()

    def test_str_method(self):
        self.assertEqual(str(self.airplane_type), "Boeing 747")


class AirplaneModelTest(TestCase):
    def setUp(self) -> None:
        self.airplane_type = sample_airplane_type()
        self.airplane = sample_airplane(airplane_type=self.airplane_type)

    def test_str_method(self):
        self.assertEqual(
            str(self.airplane),
            f"{self.airplane.name} ({self.airplane_type.name})"
        )

    def test_rows_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            sample_airplane(rows=0)

    def test_seats_in_row_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            sample_airplane(seats_in_row=0)

    def test_airplane_type_protect_on_delete(self):
        with self.assertRaises(IntegrityError):
            self.airplane_type.delete()


class AirportModelTest(TestCase):
    def setUp(self) -> None:
        self.airport = sample_airport()

    def test_str_method(self):
        self.assertEqual(
            str(self.airport),
            f"{self.airport.name} ({self.airport.closest_big_city})"
        )


class RouteModelTest(TestCase):
    def setUp(self) -> None:
        self.source = sample_airport(
            name="Kyiv Airport", closest_big_city="Kyiv")
        self.destination = sample_airport(
            name="Lviv Airport", closest_big_city="Lviv")
        self.route = sample_route(
            source=self.source, destination=self.destination)

    def test_str_method(self):
        self.assertEqual(
            str(self.route),
            (f"{self.source.name} → {self.destination.name} "
             f"({self.route.distance} km)")
        )

    def test_distance_must_be_positive(self):
        with self.assertRaises(ValidationError):
            sample_route(
                source=self.source,
                destination=self.destination,
                distance=0
            )

    def test_clean_raises_error_if_source_inactive(self):
        self.source.is_active = False
        self.source.save()
        route = Route(
            source=self.source,
            destination=self.destination,
            distance=100,
        )
        with self.assertRaises(ValidationError):
            route.clean()

    def test_save_calls_full_clean(self):
        self.source.is_active = False
        self.source.save()
        route = Route(
            source=self.source,
            destination=self.destination,
            distance=100,
        )
        with self.assertRaises(ValidationError):
            route.save()


class CrewModelTest(TestCase):
    def setUp(self) -> None:
        self.crew = sample_crew()

    def test_str_method(self):
        self.assertEqual(
            str(self.crew),
            (f"{self.crew.first_name} {self.crew.last_name} "
             f"({self.crew.get_role_display()})")
        )


class FlightModelTest(TestCase):
    def setUp(self) -> None:
        self.route = sample_route()
        self.airplane = sample_airplane()
        self.flight = sample_flight(route=self.route, airplane=self.airplane)

    def test_str_method(self):
        expected = (
            f"{self.route.source.name} → {self.route.destination.name} "
            f"| {self.flight.departure_time:%Y-%m-%d %H:%M} "
            f"| {self.airplane.name}"
        )
        self.assertEqual(str(self.flight), expected)

    def test_validate_time_raises_error(self):
        departure = timezone.now()
        arrival = departure - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            Flight.validate_time(departure, arrival)

    def test_clean_raises_error_if_airplane_inactive(self):
        self.airplane.is_active = False
        self.airplane.save()
        flight = Flight(
            route=self.route,
            airplane=self.airplane,
            departure_time=timezone.now(),
            arrival_time=timezone.now() + timedelta(hours=1)
        )
        with self.assertRaises(ValidationError):
            flight.clean()

    def test_save_calls_full_clean(self):
        departure = timezone.now()
        arrival = departure
        flight = Flight(
            route=self.route,
            airplane=self.airplane,
            departure_time=departure,
            arrival_time=arrival,
        )
        with self.assertRaises(ValidationError):
            flight.save()


class OrderModelTest(TestCase):
    def setUp(self) -> None:
        self.user = sample_user()
        self.order = sample_order(user=self.user)

    def test_str_method(self):
        expected = (
            f"Order #{self.order.pk} by {self.user} "
            f"on {self.order.created_at:%Y-%m-%d %H:%M}"
        )
        self.assertEqual(str(self.order), expected)


class TicketModelTest(TestCase):
    def setUp(self) -> None:
        self.flight = sample_flight()
        self.order = sample_order()
        self.ticket = sample_ticket(flight=self.flight, order=self.order)

    def test_str_method(self):
        expected = (
            f"{self.flight.route.source.name} "
            f"→ {self.flight.route.destination.name} "
            f"| {self.flight.departure_time:%Y-%m-%d %H:%M} "
            f"| Row {self.ticket.row}, Seat {self.ticket.seat}"
        )
        self.assertEqual(str(self.ticket), expected)

    def test_validate_row_out_of_range(self):
        airplane = self.flight.airplane
        with self.assertRaises(ValidationError):
            Ticket.validate_row(airplane.rows + 1, airplane.rows)

    def test_validate_seat_out_of_range(self):
        airplane = self.flight.airplane
        with self.assertRaises(ValidationError):
            Ticket.validate_seat(
                airplane.seats_in_row + 1,
                airplane.seats_in_row
            )

    def test_clean_invalid_row(self):
        ticket = Ticket(
            row=self.flight.airplane.rows + 1,
            seat=1,
            flight=self.flight,
            order=self.order,
        )
        with self.assertRaises(ValidationError):
            ticket.clean()

    def test_save_calls_full_clean(self):
        ticket = Ticket(
            row=self.flight.airplane.rows + 1,
            seat=1,
            flight=self.flight,
            order=self.order,
        )
        with self.assertRaises(ValidationError):
            ticket.save()
