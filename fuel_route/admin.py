from django.contrib import admin

from fuel_route.models import TruckStop


@admin.register(TruckStop)
class TruckStopAdmin(admin.ModelAdmin):
    list_display = ("opis_id", "name", "address", "city", "state", "rack_id", "retail_price", "latitude", "longitude")
