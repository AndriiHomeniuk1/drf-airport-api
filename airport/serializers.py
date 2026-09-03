from django.db import transaction
from rest_framework import serializers

from airport.validators import validate_is_active
from airport.models import (
    AirplaneType,
    Airplane,
    Airport,
    Route,
    Crew,
    Flight,
    Ticket,
    Order
)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
        )


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.CharField(
        source="airplane_type.name",
        read_only=True
    )


class AirplaneRetrieveSerializer(AirplaneSerializer):
    airplane_type = AirplaneTypeSerializer(read_only=True)



class AirportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    source = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.filter(is_active=True)
    )
    destination = serializers.PrimaryKeyRelatedField(
        queryset=Airport.objects.filter(is_active=True)
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")

    def validate(self, attrs):
        source = attrs.get("source", getattr(self.instance, "source", None))
        destination = attrs.get(
            "destination", getattr(self.instance, "destination", None))

        validate_is_active(
            "source",
            source,
            serializers.ValidationError
        )
        validate_is_active(
            "destination",
            destination,
            serializers.ValidationError
        )
        return attrs


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    destination = serializers.CharField(
        source="destination.name", read_only=True)


class RouteRetrieveSerializer(RouteSerializer):
    source = AirportSerializer(read_only=True)
    destination = AirportSerializer(read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "role")


class CrewListSerializer(CrewSerializer):
    role = serializers.CharField(source="get_role_display", read_only=True)


class FlightSerializer(serializers.ModelSerializer):
    route = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.filter(
            is_active=True
        ).select_related("source", "destination")
    )
    airplane = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.filter(
            is_active=True
        ).select_related("airplane_type")
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew"
        )

    def validate(self, attrs):
        departure_time = attrs.get(
            "departure_time",getattr(self.instance, "departure_time", None))
        arrival_time = attrs.get(
            "arrival_time", getattr(self.instance, "arrival_time", None))
        route = attrs.get("route", getattr(self.instance, "route", None))
        airplane = attrs.get(
            "airplane", getattr(self.instance, "airplane", None))

        Flight.validate_time(
            departure_time,
            arrival_time,
            serializers.ValidationError
        )
        validate_is_active(
            "route",
            route,
            serializers.ValidationError
        )
        validate_is_active(
            "airplane",
            airplane,
            serializers.ValidationError
        )
        return attrs


class FlightListSerializer(serializers.ModelSerializer):
    route = serializers.StringRelatedField()
    airplane = serializers.CharField(source="airplane.name", read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
        )


class FlightRetrieveSerializer(FlightSerializer):
    route = RouteRetrieveSerializer(read_only=True)
    airplane = AirplaneRetrieveSerializer(read_only=True)
    crew = CrewListSerializer(many=True, read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    flight = serializers.PrimaryKeyRelatedField(
        queryset=Flight.objects.select_related("airplane")
    )

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")

    def validate(self, attrs):
        row = attrs.get("row", getattr(self.instance, "row", None))
        seat = attrs.get("seat", getattr(self.instance, "seat", None))
        flight = attrs.get("flight", getattr(self.instance, "flight", None))

        Ticket.validate_row(
            row,
            flight.airplane.rows,
            serializers.ValidationError
        )
        Ticket.validate_seat(
            seat,
            flight.airplane.seats_in_row,
            serializers.ValidationError
        )
        return attrs


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(read_only=True)


class TicketRetrieveSerializer(TicketSerializer):
    flight = FlightRetrieveSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)

            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)

            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(read_only=True, many=True)


class OrderRetrieveSerializer(OrderSerializer):
    tickets = TicketRetrieveSerializer(read_only=True, many=True)
