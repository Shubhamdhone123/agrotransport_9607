from django.db import models
from django.utils import timezone
import secrets


class customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=50)
    number = models.IntegerField()
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.IntegerField()
    password = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Booking(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    BOOKING_STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(customer, on_delete=models.CASCADE, null=True)
    pickup = models.CharField(max_length=100)
    delivery = models.CharField(max_length=100)
    goodtype = models.CharField(max_length=100)
    vehicletype = models.CharField(max_length=100)
    pickupdate = models.DateField()
    distance = models.IntegerField()
    amount = models.CharField(max_length=5000000)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)

    # ── NEW: Delivery Tracking ──────────────────────────────────────────────
    booking_status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='confirmed'
    )
    driver_name = models.CharField(max_length=100, null=True, blank=True)
    driver_phone = models.CharField(max_length=15, null=True, blank=True)
    driver_lat = models.FloatField(null=True, blank=True)   # live latitude
    driver_lng = models.FloatField(null=True, blank=True)   # live longitude
    last_location_update = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    special_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # Unique secret key for driver's live location sharing link
    driver_share_key = models.CharField(max_length=64, null=True, blank=True, unique=True)

    def save(self, *args, **kwargs):
        # Auto-generate a unique key when first created
        if not self.driver_share_key:
            self.driver_share_key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.id} - {self.pickup} → {self.delivery}"


class ContactQuery(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    subject = models.CharField(max_length=200, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
