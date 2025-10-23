from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class Vehicle(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    license_plate = models.CharField(max_length=20)
    color = models.CharField(max_length=30, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Normalize input: remove extra spaces and uppercase
        raw_plate = self.license_plate.upper().strip()
        plate = re.sub(r'\s+', '', raw_plate)

        print(f"DEBUG LICENSE PLATE INPUT: '{raw_plate}' -> '{plate}'")

        # Accept both 'ABC123' / 'ABC 123' and '123ABC' / '123 ABC'
        patterns = [
            r'^[A-Z]{2,3}\s?\d{2,3}$',  # ABC123 or ABC 123
            r'^\d{2,3}\s?[A-Z]{2,3}$',  # 123ABC or 123 ABC
        ]

        if not any(re.match(pattern, raw_plate) or re.match(pattern, plate) for pattern in patterns):
            raise ValidationError("Invalid Lebanese license plate format. Use format like: 123 ABC or ABC 123")

        # Reformat for storage (always 'XXX 123' or '123 XXX')
        if re.match(r'^([A-Z]{2,3})(\d{2,3})$', plate):
            self.license_plate = re.sub(r'^([A-Z]{2,3})(\d{2,3})$', r'\1 \2', plate)
        elif re.match(r'^(\d{2,3})([A-Z]{2,3})$', plate):
            self.license_plate = re.sub(r'^(\d{2,3})([A-Z]{2,3})$', r'\1 \2', plate)

    def save(self, *args, **kwargs):
        # Run validation before saving
        self.full_clean()

        # Normalize again before saving
        self.license_plate = re.sub(r'\s+', ' ', self.license_plate.upper().strip())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.make} {self.model} - {self.license_plate}"


class ParkingLot(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)
    daily_rate = models.DecimalField(max_digits=6, decimal_places=2)
    monthly_rate = models.DecimalField(max_digits=8, decimal_places=2)
    total_spots = models.PositiveIntegerField()
    available_spots = models.PositiveIntegerField()
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    features = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def is_open(self):
        from datetime import datetime
        current_time = datetime.now().time()
        return self.opening_time <= current_time <= self.closing_time


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
    qr_code = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.parking_lot.name}"
