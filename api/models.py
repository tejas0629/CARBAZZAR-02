from django.db import models

class Vehicle(models.Model):
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.CharField(max_length=100, blank=True, null=True)
    fuel_type = models.CharField(max_length=50, blank=True, null=True)
    engine = models.CharField(max_length=100, blank=True, null=True)
    power = models.CharField(max_length=100, blank=True, null=True)
    mileage = models.CharField(max_length=100, blank=True, null=True)
    transmission = models.CharField(max_length=100, blank=True, null=True)
    seating_capacity = models.IntegerField(blank=True, null=True)

    central_locking = models.BooleanField(default=False)
    air_conditioner = models.BooleanField(default=False)
    power_windows = models.BooleanField(default=False)
    keyless_entry = models.BooleanField(default=False)
    bluetooth = models.BooleanField(default=False)
    android_auto = models.BooleanField(default=False)
    steering_controls = models.BooleanField(default=False)

    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)

    def __str__(self):
        return f"{self.brand} {self.name}"
