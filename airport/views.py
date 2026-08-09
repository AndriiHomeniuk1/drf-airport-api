from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, OpenApiResponse

from airport.models import (
    AirplaneType,
    Airplane,
    Airport,
    Route,
    Crew,
    Flight,
    Order
)

from airport.serializers import (
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneRetrieveSerializer,
    AirportSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    CrewSerializer,
    CrewListSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightRetrieveSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderRetrieveSerializer,
)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer

        if self.action == "retrieve":
            return AirplaneRetrieveSerializer

        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(is_active=True)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related()

        return queryset.order_by("id")

    @extend_schema(
        description="Deactivate the airplane (soft delete).",
        responses={
            204: OpenApiResponse(
                description="Airplane deactivated successfully."
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        airplane = self.get_object()
        airplane.is_active = False
        airplane.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects
    serializer_class = AirportSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(is_active=True)
        return queryset.order_by("id")

    @extend_schema(
        description="Deactivate the airport (soft delete).",
        responses={
            204: OpenApiResponse(
                description="Airport deactivated successfully."
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        airport = self.get_object()
        airport.is_active = False
        airport.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteRetrieveSerializer

        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset.filter(is_active=True)

        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related()

        return queryset.order_by("id")

    @extend_schema(
        description="Deactivate the route (soft delete).",
        responses={
            204: OpenApiResponse(
                description="Route deactivated successfully."
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        route = self.get_object()
        route.is_active = False
        route.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects
    serializer_class = CrewSerializer

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return CrewListSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset
        return queryset.order_by("id")


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightRetrieveSerializer

        return self.serializer_class

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.select_related(
                "route__source",
                "route__destination",
                "airplane",
            )
        if self.action == "retrieve":
            queryset = queryset.select_related(
                "route__source",
                "route__destination",
                "airplane__airplane_type",
            ).prefetch_related("crew")

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
                "tickets__flight__airplane",
            )

        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
                "tickets__flight__airplane__airplane_type",
                "tickets__flight__crew",
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        serializer = self.serializer_class

        if self.action == "list":
            serializer = OrderListSerializer

        if self.action == "retrieve":
            serializer = OrderRetrieveSerializer

        return serializer
