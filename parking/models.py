from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from io import BytesIO
from django.core.files import File
from django.urls import reverse
import re
import qrcode


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
        compact_plate = re.sub(r'\s+', '', raw_plate)

        match = re.fullmatch(r'([A-Z])(\d{2,8})', compact_plate or '')
        if not match:
            raise ValidationError("Invalid Lebanese license plate format. Use format like: B 123456")

        self.license_plate = f"{match.group(1)} {match.group(2)}"

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
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_parking_lots', null=True, blank=True)
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
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.parking_lot.name}"
    
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    checked_in = models.BooleanField(default=False)

    def generate_qr_code(self):
        import qrcode
        from io import BytesIO
        from django.core.files import File
        from django.conf import settings

        check_in_url = reverse('parking:check_in', args=[self.id])
        full_url = f"http://127.0.0.1:8000{check_in_url}"  # Change to your domain

        # Generate a high quality QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format='PNG')
        self.qr_code.save(f"reservation_{self.id}.png", File(buffer), save=False)
        buffer.close()

    @classmethod
    def auto_refresh_statuses(cls) -> None:
        """
        Synchronize reservation statuses with their scheduled windows.

        - Pending/confirmed reservations that are currently in their booking window become active.
        - Active reservations that have ended remain active only if the driver checked in; otherwise they expire.
        - Checked-in reservations that have ended transition to completed once their window has elapsed.
        """
        from django.utils import timezone

        now = timezone.now()

        # Promote upcoming reservations to active when their window begins.
        cls.objects.filter(
            status__in=['pending', 'confirmed'],
            start_time__lte=now,
            end_time__gt=now,
        ).update(status='active')

        # Mark checked-in reservations as completed when their window ends.
        cls.objects.filter(
            status__in=['pending', 'confirmed', 'active'],
            end_time__lte=now,
            checked_in=True,
        ).update(status='completed')

        # Any other overdue reservations expire automatically.
        cls.objects.filter(
            status__in=['pending', 'confirmed', 'active'],
            end_time__lte=now,
            checked_in=False,
        ).update(status='expired')
