from django.db import models

# Create your models here.
class TruckStop(models.Model):
    opis_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=2)
    rack_id = models.IntegerField()
    retail_price = models.DecimalField(max_digits=6, decimal_places=2)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['retail_price']),
            models.Index(fields=['state']),
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"

    def get_location_tuple(self):
        """Return location as a tuple for distance calculations."""
        return self.latitude, self.longitude
