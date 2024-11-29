from typing import List, Dict, Tuple

import googlemaps
from django.conf import settings
from django.db import models
from django.views.generic import TemplateView
from geopy.distance import geodesic
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from fuel_route.models import TruckStop


class HomePageView(TemplateView):
    template_name = 'index.html'


class OptimalRouteView(APIView):
    """
    API endpoint to calculate optimal route with fuel stops
    """
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
        self.MAX_RANGE = 500  # Maximum range in miles
        self.MPG = 10  # Average miles per gallon

    def post(self, request, *args, **kwargs) -> Response:
        """
        POST method to calculate optimal route
        :param request: Expected input: {
            "start_location": "Start City, State",
            "end_location": "End City, State",
        }
        :return: Response with optimal route and fuel stops
        """
        start_location = request.data.get('start_location')
        end_location = request.data.get('end_location')

        # Validate input
        if not start_location or not end_location:
            return Response({
                "error": "Missing required fields: start_location, end_location"
            }, status=400)

        route_data = self.calculate_optimal_route(start_location, end_location)

        return Response(route_data, status=status.HTTP_200_OK)

    def calculate_optimal_route(self, start_location: str, end_location: str) -> Dict:
        directions = self.gmaps.directions(
            start_location,
            end_location,
            mode="driving",
            alternatives=False
        )

        if not directions:
            raise ValueError("No route found between specified locations")

        route = directions[0]
        total_distance = route['legs'][0]['distance']['value'] * 0.000621371    # Convert to miles
        duration = route['legs'][0]['duration']['text']

        path = route['overview_polyline']['points']
        route_coords = googlemaps.convert.decode_polyline(path)

        fuel_stops = self.find_fuel_stops(route_coords)

        total_gallons = total_distance / self.MPG
        total_cost = self.calculate_total_fuel_cost(total_gallons, fuel_stops)

        return {
            "route": {
                "coordinates": route_coords,
                "total_distance_miles": round(total_distance, 2),
                "duration": duration
            },
            "fuel_stops": [
                {
                    "name": stop.name,
                    "location": {
                        "lat": stop.latitude,
                        "lng": stop.longitude
                    },
                    "price": float(stop.retail_price),
                    "distance_from_start": distance
                } for stop, distance in fuel_stops
            ],
            "summary": {
                "total_cost": round(total_cost, 2),
                "total_gallons": round(total_gallons, 2),
                "number_of_stops": len(fuel_stops)
            }
        }

    def find_fuel_stops(self, route_coords: List[Dict]) -> List[Tuple[TruckStop, float]]:
        """
        Find final fuel stops along the route
        :param route_coords: List of coordinates along the route
        :return: List of fuel stops with distance from start
        """
        fuel_stops = []
        current_distance = 0
        last_fuel_point = (route_coords[0]['lat'], route_coords[0]['lng'])

        BUFFER_DISTANCE = self.MAX_RANGE * 0.8  # starts looking for fuels when 80% of range is covered

        for point in route_coords[1:]:
            current_point = (point['lat'], point['lng'])

            # distance from last point
            segment_distance = geodesic(last_fuel_point, current_point).miles
            current_distance += segment_distance

            if current_distance >= BUFFER_DISTANCE:
                # Get nearby stops with their minimum fuel price
                nearby_stops = TruckStop.objects.filter(
                    latitude__gte=min(point['lat'] - 0.5, point['lat'] + 0.5),
                    latitude__lte=max(point['lat'] - 0.5, point['lat'] + 0.5),
                    longitude__gte=min(point['lng'] - 0.5, point['lng'] + 0.5),
                    longitude__lte=max(point['lng'] - 0.5, point['lng'] + 0.5),
                    fuel_prices__isnull=False  # Ensure stops have prices
                ).annotate(
                    min_price=models.Min('fuel_prices__price')  # Get minimum price for each stop
                ).order_by('min_price')[:10]

                if nearby_stops:
                    best_stop = None
                    best_score = float('inf')

                    for stop in nearby_stops:
                        stop_point = (stop.latitude, stop.longitude)
                        deviation = geodesic(last_fuel_point, stop_point).miles
                        price_factor = float(stop.min_price)
                        score = (price_factor * 0.7) + (deviation * 0.3)

                        if score < best_score:
                            best_score = score
                            best_stop = stop

                    if best_stop:
                        fuel_stops.append((best_stop, current_distance))
                        last_fuel_point = (best_stop.latitude, best_stop.longitude)
                        current_distance = 0

        return fuel_stops

    def calculate_total_fuel_cost(self, total_gallons: float, fuel_stops: List[Tuple[TruckStop, float]]) -> float:
        """
        Calculate total fuel cost based on fuel stops
        :param total_gallons: Total gallons required for the trip
        :param fuel_stops: List of fuel stops with distance from start
        :return: Total cost of fuel for the trip
        """
        total_cost = 0
        remaining_gallons = total_gallons

        for i, (stop, distance) in enumerate(fuel_stops):
            segment_gallons = (distance / self.MPG)

            if i == len(fuel_stops) - 1:
                segment_gallons = remaining_gallons

            segment_cost = segment_gallons * float(stop.retail_price)
            total_cost += segment_cost
            remaining_gallons -= segment_gallons

        return total_cost
