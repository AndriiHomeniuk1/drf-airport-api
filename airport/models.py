from django.db import models
from django.conf import settings
from django.db.models.constraints import UniqueConstraint
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db.models import Q


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
    rows = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    seats_in_row = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    airplane_type = models.ForeignKey(
        AirplaneType, on_delete=models.PROTECT, related_name="airplanes")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(rows__gt=0),
                name="check_airplane_rows_gt_0"
            ),
            models.CheckConstraint(
                condition=Q(seats_in_row__gt=0),
                name="check_airplane_seats_in_row_gt_0"
            )
        ]

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
    distance = models.IntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["source", "destination"])
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(distance__gt=0),
                name="check_route_distance_gt_0"
            )
        ]

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

    class Meta:
        indexes = [
            models.Index(fields=["departure_time"])
        ]

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

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["flight", "row", "seat"],
                name="unique_seat_per_flight"
            )
        ]
        ordering = ("flight", "row", "seat")

    @staticmethod
    def validate_row(row: int, airplane_rows: int) -> None:
        if not (1 <= row <= airplane_rows):
            raise ValidationError(
                {
                    "row":(
                        f"Row must be in range [1, {airplane_rows}], "
                        f"not {row}."
                    )
                }
            )

    @staticmethod
    def validate_seat(seat: int, seats_in_row: int) -> None:
        if not (1 <= seat <= seats_in_row):
            raise ValidationError(
                {
                    "seat": (
                        f"Seat must be in range [1, {seats_in_row}], "
                        f"not {seat}."
                    )
                }
            )

    def clean(self):
        if self.flight_id is None:
            return

        airplane = self.flight.airplane

        self.validate_row(self.row, airplane.rows)
        self.validate_seat(self.seat, airplane.seats_in_row)

    def save(
        self,
        force_insert = False,
        force_update = False,
        using = None,
        update_fields = None,
    ):
        self.full_clean()
        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

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

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Order #{self.id} by {self.user} "
            f"on {self.created_at:%Y-%m-%d %H:%M}"
        )
