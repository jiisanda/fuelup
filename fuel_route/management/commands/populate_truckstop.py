import csv
import re
import time
from math import cos, radians, sin

from django.core.management import BaseCommand
from geopy.geocoders import Nominatim

from fuel_route.models import TruckStop


class Command(BaseCommand):
    help = "Populate the TruckStop model with data from the OPIS database"

    def __init__(self):
        super().__init__()
        self.geolocator = Nominatim(user_agent="fuel_route_app")

        # Common Interstate orientations (approximate)
        self.highway_directions = {
            'I-5': 0,  # North-South
            'I-10': 90,  # East-West
            'I-15': 0,  # North-South
            'I-20': 90,  # East-West
            'I-25': 0,  # North-South
            'I-35': 0,  # North-South
            'I-40': 90,  # East-West
            'I-44': 45,  # Northeast-Southwest
            'I-70': 90,  # East-West
            'I-75': 0,  # North-South
            'I-80': 90,  # East-West
            'I-90': 90,  # East-West
            'I-95': 0,  # North-South
        }

    def extract_highway_info(self, address: str) -> tuple:
        """Extract highway number and exit number from address."""
        highway_match = re.search(r'I-(\d+)', address)
        exit_match = re.search(r'EXIT (\d+)', address)

        highway_num = highway_match.group(1) if highway_match else None
        exit_num = exit_match.group(1) if exit_match else None

        return f'I-{highway_num}' if highway_num else None, exit_num

    def calculate_exit_coordinates(self, city_lat: float, city_lon: float,
                                   highway: str, exit_num: str,
                                   offset_miles: float = 2.0) -> tuple:
        """
        Calculate approximate exit coordinates based on highway orientation
        and exit number. This is a rough approximation.
        """
        if not highway or not exit_num:
            return city_lat, city_lon

        # Get highway direction (0 = N/S, 90 = E/W)
        direction = self.highway_directions.get(highway, 45)

        # Convert offset to approximate degrees
        lat_offset = offset_miles / 69.0  # 1 degree lat ≈ 69 miles
        lon_offset = offset_miles / (69.0 * cos(radians(city_lat)))

        # Calculate offsets based on highway direction
        if direction == 0:  # N/S highway
            return city_lat, city_lon + lon_offset
        elif direction == 90:  # E/W highway
            return city_lat + lat_offset, city_lon
        else:  # Diagonal highway
            angle = radians(direction)
            return (
                city_lat + (lat_offset * sin(angle)),
                city_lon + (lon_offset * cos(angle))
            )

    def geocode_address(self, address: str, city: str, state: str) -> tuple:
        """Geocode truck stop location using city as base and calculating offset."""
        try:
            # First get city coordinates
            city_location = self.geolocator.geocode(f"{city}, {state}, USA", exactly_one=True)
            if not city_location:
                self.stdout.write(self.style.ERROR(f"Could not geocode city: {city}, {state}"))
                return None, None

            city_lat, city_lon = city_location.latitude, city_location.longitude

            # Extract highway and exit info
            highway, exit_num = self.extract_highway_info(address)

            # Calculate approximate exit location
            if highway and exit_num:
                final_lat, final_lon = self.calculate_exit_coordinates(
                    city_lat, city_lon, highway, exit_num
                )
                self.stdout.write(self.style.SUCCESS(
                    f"Calculated coordinates for {highway} Exit {exit_num}: {final_lat}, {final_lon}"
                ))
                return final_lat, final_lon

            return city_lat, city_lon

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Geocoding error: {str(e)}"))
            return None, None

    def handle(self, *args, **options):
        csv_file_path = "data/fuel-prices.csv"

        try:
            with open(csv_file_path, mode='r') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        retail_price = float(row['Retail Price'].strip())
                    except ValueError:
                        continue

                    lat, lon = self.geocode_address(
                        row['Address'],
                        row['City'],
                        row['State']
                    )

                    if lat is None or lon is None:
                        continue

                    time.sleep(1)  # Rate limiting

                    try:
                        _, created = TruckStop.objects.get_or_create(
                            opis_id=int(row['OPIS Truckstop ID']),
                            defaults={
                                'name': row['Truckstop Name'].strip(),
                                'address': row['Address'].strip(),
                                'city': row['City'].strip(),
                                'state': row['State'].strip(),
                                'rack_id': int(row['Rack ID']),
                                'retail_price': retail_price,
                                'latitude': lat,
                                'longitude': lon
                            },
                        )
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Database error: {str(e)}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
