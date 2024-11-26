import csv

from django.core.management import BaseCommand

from fuel_route.models import TruckStop


class Command(BaseCommand):
    help = "Populate the TruckStop model with data from the OPIS database"

    def handle(self, *args, **options):
        csv_file_path = "data/fuel-prices.csv"

        if TruckStop.objects.exists():
            self.stdout.write(self.style.WARNING("TruckStop data already populated."))
            return

        try:
            with open(csv_file_path, mode='r') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    # Use get_or_create to prevent duplicate entries
                    _, created = TruckStop.objects.get_or_create(
                        opis_id=row['OPIS Truckstop ID'],
                        defaults={
                            'name': row['Truckstop Name'],
                            'address': row['Address'],
                            'city': row['City'],
                            'state': row['State'],
                            'rack_id': row['Rack ID'],
                            'retail_price': row['Retail Price'],
                        },
                    )
                    if created:
                        continue
                    else:
                        self.stdout.write(self.style.WARNING(f"Skipped (already exists): {row['Truckstop Name']}"))

            self.stdout.write(self.style.SUCCESS("TruckStop data population complete."))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file_path}"))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f"Missing column in CSV: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
