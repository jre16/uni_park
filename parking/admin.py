from django.contrib import admin
from .models import StudentProfile, Vehicle, ParkingLot, Reservation

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'email_verified', 'phone_verified', 'created_at']
    list_filter = ['email_verified', 'phone_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['student', 'make', 'model', 'year', 'license_plate', 'color', 'is_primary', 'created_at']
    list_filter = ['make', 'year', 'is_primary', 'created_at']
    search_fields = ['make', 'model', 'license_plate', 'student__user__username']
    readonly_fields = ['created_at']

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'address', 'hourly_rate', 'daily_rate', 'available_spots', 'total_spots', 'is_active']
    list_filter = ['is_active', 'hourly_rate', 'owner']
    search_fields = ['name', 'address', 'owner__username', 'owner__email']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'owner', 'address', 'is_active')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Pricing', {
            'fields': ('hourly_rate', 'daily_rate', 'monthly_rate')
        }),
        ('Availability', {
            'fields': ('total_spots', 'available_spots')
        }),
        ('Hours', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Additional Info', {
            'fields': ('features',)
        })
    )

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['student', 'vehicle', 'parking_lot', 'status', 'start_time', 'end_time', 'total_cost', 'created_at']
    list_filter = ['status', 'created_at', 'start_time']
    search_fields = ['student__user__username', 'vehicle__license_plate', 'parking_lot__name']
    readonly_fields = ['created_at', 'qr_code']
    
    fieldsets = (
        ('Reservation Details', {
            'fields': ('student', 'vehicle', 'parking_lot', 'status')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Payment', {
            'fields': ('total_cost',)
        }),
        ('Access', {
            'fields': ('qr_code',)
        })
    )