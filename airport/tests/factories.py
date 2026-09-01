from datetime import timedelta

from django.contrib.auth import get_user_model
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
