from decimal import Decimal
from typing import Optional

from django.db import models


class TruckStop(models.Model):
    opis_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=2)
    rack_id = models.IntegerField()
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['state']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"

    def get_location_tuple(self):
        return self.latitude, self.longitude

    @property
    def retail_price(self) -> Optional[Decimal]:
        """Get the current lowest price for this truck stop"""
        latest_price = self.fuel_prices.order_by('price').first()
        return latest_price.price if latest_price else None


class FuelPrice(models.Model):
    truck_stop = models.ForeignKey(
        TruckStop,
        related_name='fuel_prices',
        on_delete=models.CASCADE
    )
    price = models.DecimalField(max_digits=6, decimal_places=3)

    def __str__(self):
        return f"{self.truck_stop.name} - {self.price}"

    class Meta:
        indexes = [
            models.Index(fields=['price']),
        ]
