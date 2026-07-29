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
