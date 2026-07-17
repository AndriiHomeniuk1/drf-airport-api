from django.db import models
from django.conf import settings


class CrewRole(models.TextChoices):
    PILOT = "pilot", "Pilot"
    COPILOT = "copilot", "Co-Pilot"
    ATTENDANT = "attendant", "Flight Attendant"


class AirplaneType(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=64, unique=True)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType, on_delete=models.PROTECT, related_name="airplanes")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.airplane_type.name})"


class Airport(models.Model):
    name = models.CharField(max_length=64, unique=True)
    closest_big_city = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.closest_big_city})"


class Route(models.Model):
    source = models.ForeignKey(
        Airport, on_delete=models.PROTECT, related_name="source_routes")
    destination = models.ForeignKey(
        Airport, on_delete=models.PROTECT, related_name="destination_routes")
    distance = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return (
            f"{self.source.name} → {self.destination.name} "
            f"({self.distance} km)"
        )


class Crew(models.Model):
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    role = models.CharField(max_length=32, choices=CrewRole.choices)

    def __str__(self):
        return (
            f"{self.first_name} {self.last_name} ({self.get_role_display()})"
        )


class Flight(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.PROTECT, related_name="flights")
    airplane = models.ForeignKey(
        Airplane, on_delete=models.PROTECT, related_name="flights")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, related_name="flights", blank=True)

    def __str__(self):
        return (
            f"{self.route.source.name} "
            f"→ {self.route.destination.name} "
            f"| {self.departure_time:%Y-%m-%d %H:%M} | {self.airplane.name}"
        )


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="tickets")

    def __str__(self):
        return (
            f"{self.flight.route.source.name} "
            f"→ {self.flight.route.destination.name} "
            f"| {self.flight.departure_time:%Y-%m-%d %H:%M} "
            f"| Row {self.row}, Seat {self.seat}"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return (
            f"Order #{self.id} by {self.user} "
            f"on {self.created_at:%Y-%m-%d %H:%M}"
        )
