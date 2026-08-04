from django.db import transaction
from rest_framework import serializers

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

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(source="source.name", read_only=True)
    destination = serializers.CharField(source="destination.name", read_only=True)


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
        queryset=Route.objects.select_related("source", "destination")
    )
    airplane = serializers.PrimaryKeyRelatedField(
        queryset=Airplane.objects.select_related("airplane_type")
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
        Flight.validate_time(
            attrs["departure_time"],
            attrs["arrival_time"],
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
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")

    def validate(self, attrs):
        Ticket.validate_row(
            attrs["row"],
            attrs["flight"].airplane.rows,
            serializers.ValidationError
        )
        Ticket.validate_seat(
            attrs["seat"],
            attrs["flight"].airplane.seats_in_row,
            serializers.ValidationError
        )
        return attrs


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
