from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
<<<<<<< HEAD
from django.utils import timezone
from datetime import timedelta
=======
from io import BytesIO
from django.core.files import File
from django.urls import reverse
>>>>>>> 7464572b2ec20b2a2d6425255ea0e61e92ef9e9e
import re
import qrcode


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    features = models.TextField()
    perks = models.JSONField(default=list)  # Store perks as a list of dictionaries
    color_theme = models.CharField(max_length=50, default='primary')  # For UI styling
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (${self.price}/month)"


class StudentSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('grace_period', 'Grace Period'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    student = models.ForeignKey('StudentProfile', on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    grace_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")
        if self.grace_period_end and self.grace_period_end <= self.end_date:
            raise ValidationError("Grace period must extend beyond subscription end date")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_valid(self):
        now = timezone.now()
        if self.status == 'active':
            return now <= self.end_date
        elif self.status == 'grace_period':
            return now <= self.grace_period_end if self.grace_period_end else False
        return False

    def enter_grace_period(self, days=7):
        if self.status == 'active' and self.end_date <= timezone.now():
            self.status = 'grace_period'
            self.grace_period_end = self.end_date + timedelta(days=days)
            self.save()

    def cancel(self):
        if self.status in ['active', 'grace_period']:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.auto_renew = False
            self.save()

    def reactivate(self):
        if self.status in ['paused', 'cancelled'] and timezone.now() <= self.end_date:
            self.status = 'active'
            self.cancelled_at = None
            self.save()

    def __str__(self):
        return f"{self.student.user.username}'s {self.plan.name} Subscription ({self.status})"


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

    PAYMENT_TYPE_CHOICES = [
        ('one_time', 'One-time Payment'),
        ('subscription', 'Subscription'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_cost = models.DecimalField(max_digits=8, decimal_places=2)
<<<<<<< HEAD
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='one_time')
    subscription = models.ForeignKey(StudentSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    qr_code = models.CharField(max_length=100, blank=True, null=True)
=======
>>>>>>> 7464572b2ec20b2a2d6425255ea0e61e92ef9e9e
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.payment_type == 'subscription':
            if not self.subscription:
                raise ValidationError("Subscription is required for subscription-based reservations")
            if not self.subscription.is_valid():
                raise ValidationError("Subscription is not active or has expired")

    def save(self, *args, **kwargs):
        if self.payment_type == 'subscription':
            # No cost for subscription-based reservations
            self.total_cost = 0
        self.full_clean()
        super().save(*args, **kwargs)

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

        # Generate the QR code image
        qr = qrcode.make(full_url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        self.qr_code.save(f"reservation_{self.id}.png", File(buffer), save=False)
        buffer.close()
