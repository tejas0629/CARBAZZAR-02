from django.db import models

class Vehicle(models.Model):
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    # Price variants
    base_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mid_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    top_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Keep old price field for backward compatibility
    price = models.CharField(max_length=100, blank=True, null=True)
    
    fuel_type = models.CharField(max_length=50, blank=True, null=True)
    engine = models.CharField(max_length=100, blank=True, null=True)
    power = models.CharField(max_length=100, blank=True, null=True)
    mileage = models.CharField(max_length=100, blank=True, null=True)
    transmission = models.CharField(max_length=100, blank=True, null=True)
    seating_capacity = models.IntegerField(blank=True, null=True)
    safety_rating = models.CharField(max_length=10, blank=True, null=True)

    central_locking = models.BooleanField(default=False)
    air_conditioner = models.BooleanField(default=False)
    power_windows = models.BooleanField(default=False)
    keyless_entry = models.BooleanField(default=False)
    bluetooth = models.BooleanField(default=False)
    android_auto = models.BooleanField(default=False)
    steering_controls = models.BooleanField(default=False)

    # Keep old image field for backward compatibility
    image = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    
    # New multiple image fields
    image1 = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    image2 = models.ImageField(upload_to='vehicles/', blank=True, null=True)
    image3 = models.ImageField(upload_to='vehicles/', blank=True, null=True)

    def __str__(self):
        return f"{self.brand} {self.name}"
    
    def get_images(self):
        """Return list of all images"""
        images = []
        if self.image1:
            images.append(self.image1.url)
        if self.image2:
            images.append(self.image2.url)
        if self.image3:
            images.append(self.image3.url)
        # Fallback to old image field
        if not images and self.image:
            images.append(self.image.url)
        return images
    
    def get_base_price(self):
        """Return base price for display"""
        if self.base_price:
            return self.base_price
        return self.price if self.price else "N/A"
