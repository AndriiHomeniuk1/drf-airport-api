from rest_framework import status
from rest_framework.response import Response
from rest_framework import viewsets

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
    FlightSerializer,
    OrderSerializer,
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

    def destroy(self, request, *args, **kwargs):
        route = self.get_object()
        route.is_active = False
        route.save(update_fields=["is_active"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
