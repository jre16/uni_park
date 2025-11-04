from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import random
import string
from datetime import datetime
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from .models import StudentProfile, Vehicle, ParkingLot, Reservation
from .forms import StudentSignupForm, StudentLoginForm, VehicleForm, ParkingLotSearchForm


def home(request):
    return render(request, 'parking/home.html')


def signup(request):
    if request.method == 'POST':
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            verification_code = ''.join(random.choices(string.digits, k=6))
            profile = user.studentprofile
            profile.verification_code = verification_code
            profile.save()
            print("=" * 60)
            print(f"🔐 VERIFICATION CODE FOR {user.email.upper()}")
            print(f"📧 Email: {user.email}")
            print(f"🔑 Code: {verification_code}")
            print("=" * 60)
            messages.success(request, f'Account created successfully! Please check the terminal for your verification code.')
            return redirect('parking:verify_email')
    else:
        form = StudentSignupForm()
    return render(request, 'parking/signup.html', {'form': form})


def verify_email(request):
    if request.method == 'POST':
        code = request.POST.get('verification_code')
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = user.studentprofile
            if profile.verification_code == code:
                profile.email_verified = True
                profile.verification_code = None
                profile.save()
                messages.success(request, 'Email verified successfully! You can now log in.')
                return redirect('parking:login')
            else:
                messages.error(request, 'Invalid verification code.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return render(request, 'parking/verify_email.html')


def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = user.studentprofile
            if not profile.email_verified:
                verification_code = ''.join(random.choices(string.digits, k=6))
                profile.verification_code = verification_code
                profile.save()
                print(f"New verification code for {email}: {verification_code}")
                messages.success(request, 'New verification code sent!')
            else:
                messages.info(request, 'Email is already verified.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('parking:verify_email')


def user_login(request):
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            email_or_phone = form.cleaned_data['email_or_phone']
            password = form.cleaned_data['password']
            user = None
            if '@' in email_or_phone:
                try:
                    user = User.objects.get(email=email_or_phone)
                except User.DoesNotExist:
                    pass
            else:
                try:
                    profile = StudentProfile.objects.get(phone_number=email_or_phone)
                    user = profile.user
                except StudentProfile.DoesNotExist:
                    pass
            if user:
                authenticated_user = authenticate(username=user.username, password=password)
                if authenticated_user:
                    profile = authenticated_user.studentprofile
                    if not profile.email_verified:
                        messages.error(request, 'Please verify your email before logging in.')
                        return redirect('parking:verify_email')
                    login(request, authenticated_user)
                    messages.success(request, 'Logged in successfully!')
                    return redirect('parking:dashboard')
                else:
                    messages.error(request, 'Invalid credentials.')
            else:
                messages.error(request, 'User not found.')
    else:
        form = StudentLoginForm()
    return render(request, 'parking/login.html', {'form': form})


@login_required
def dashboard(request):
    student_profile = request.user.studentprofile
    vehicles = student_profile.vehicles.all()
    recent_reservations = Reservation.objects.filter(student=student_profile).order_by('-created_at')[:5]
    context = {
        'student': student_profile,
        'vehicles': vehicles,
        'recent_reservations': recent_reservations
    }
    return render(request, 'parking/dashboard.html', context)


@login_required
def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.student = request.user.studentprofile
            if vehicle.is_primary or not request.user.studentprofile.vehicles.exists():
                request.user.studentprofile.vehicles.update(is_primary=False)
                vehicle.is_primary = True
            vehicle.save()
            messages.success(request, 'Vehicle added successfully!')
            return redirect('parking:dashboard')
    else:
        form = VehicleForm()
    return render(request, 'parking/add_vehicle.html', {'form': form})


@login_required
def edit_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, student=request.user.studentprofile)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            updated_vehicle = form.save(commit=False)
            if updated_vehicle.is_primary:
                request.user.studentprofile.vehicles.update(is_primary=False)
                updated_vehicle.is_primary = True
            updated_vehicle.save()
            messages.success(request, 'Vehicle updated successfully!')
            return redirect('parking:dashboard')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'parking/edit_vehicle.html', {'form': form, 'vehicle': vehicle})


@login_required
def delete_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, student=request.user.studentprofile)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted successfully!')
    return redirect('parking:dashboard')


def search_parking(request):
    form = ParkingLotSearchForm(request.GET or None)
    parking_lots = ParkingLot.objects.filter(is_active=True)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        sort_by = form.cleaned_data.get('sort_by', 'distance')
        if query:
            parking_lots = parking_lots.filter(Q(name__icontains=query) | Q(address__icontains=query))
        if sort_by == 'price_low':
            parking_lots = parking_lots.order_by('hourly_rate')
        elif sort_by == 'price_high':
            parking_lots = parking_lots.order_by('-hourly_rate')
        elif sort_by == 'availability':
            parking_lots = parking_lots.order_by('-available_spots')
    context = {'form': form, 'parking_lots': parking_lots}
    return render(request, 'parking/search.html', context)


def parking_lot_detail(request, parking_lot_id):
    parking_lot = get_object_or_404(ParkingLot, id=parking_lot_id)
    return render(request, 'parking/lot_detail.html', {'parking_lot': parking_lot})


@login_required
def reserve_parking(request, parking_lot_id):
    parking_lot = get_object_or_404(ParkingLot, id=parking_lot_id)
    student_profile = request.user.studentprofile
    vehicles = student_profile.vehicles.all()

    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if not vehicle_id or not start_time or not end_time:
            messages.error(request, 'All fields are required.')
            return redirect('parking:reserve_parking', parking_lot_id=parking_lot_id)

        try:
            start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
            end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        except ValueError:
            messages.error(request, 'Invalid date or time format.')
            return redirect('parking:reserve_parking', parking_lot_id=parking_lot_id)

        if end_time <= start_time:
            messages.error(request, 'End time must be after start time.')
            return redirect('parking:reserve_parking', parking_lot_id=parking_lot_id)

        opening = parking_lot.opening_time
        closing = parking_lot.closing_time
        is_overnight = closing < opening

        if not is_overnight:
            if start_time.time() < opening or end_time.time() > closing:
                messages.error(request, f'Reservations must be within operating hours ({opening.strftime("%I:%M %p")} - {closing.strftime("%I:%M %p")}).')
                return redirect('parking:reserve_parking', parking_lot_id=parking_lot_id)
        else:
            if start_time.time() < opening and end_time.time() > closing:
                messages.error(request, f'Reservations must be within operating hours ({opening.strftime("%I:%M %p")} - {closing.strftime("%I:%M %p")}).')
                return redirect('parking:reserve_parking', parking_lot_id=parking_lot_id)

        if parking_lot.available_spots <= 0:
            messages.error(request, 'No available spots at this time.')
            return redirect('parking:parking_lot_detail', parking_lot_id=parking_lot_id)

        duration_hours = (end_time - start_time).total_seconds() / 3600
        total_cost = Decimal(duration_hours) * parking_lot.hourly_rate

        vehicle = get_object_or_404(Vehicle, id=vehicle_id, student=student_profile)
        Reservation.objects.create(
            student=student_profile,
            vehicle=vehicle,
            parking_lot=parking_lot,
            start_time=start_time,
            end_time=end_time,
            total_cost=total_cost,
            status='confirmed'
        )

        parking_lot.available_spots -= 1
        parking_lot.save()
        messages.success(
            request,
            f'Reservation confirmed from {start_time.strftime("%I:%M %p")} to {end_time.strftime("%I:%M %p")}. '
            f'Total cost: ${total_cost:.2f}.'
        )
        return redirect('parking:dashboard')

    return render(request, 'parking/reserve.html', {'parking_lot': parking_lot, 'vehicles': vehicles})



def get_nearby_parking(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = float(data.get('latitude'))
            lng = float(data.get('longitude'))
            radius = float(data.get('radius', 5))
            def haversine(lat1, lon1, lat2, lon2):
                from math import radians, sin, cos, asin, sqrt
                R = 6371
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                c = 2 * asin(sqrt(a))
                return R * c
            parking_lots = ParkingLot.objects.filter(is_active=True)
            nearby_lots = []
            for lot in parking_lots:
                if lot.latitude and lot.longitude:
                    distance = haversine(lat, lng, float(lot.latitude), float(lot.longitude))
                    if distance <= radius:
                        nearby_lots.append({
                            'id': lot.id,
                            'name': lot.name,
                            'address': lot.address,
                            'latitude': float(lot.latitude),
                            'longitude': float(lot.longitude),
                            'available_spots': lot.available_spots,
                            'hourly_rate': float(lot.hourly_rate),
                            'distance': round(distance, 2),
                        })
            nearby_lots.sort(key=lambda x: x['distance'])
            return JsonResponse({'success': True, 'parking_lots': nearby_lots})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, student=request.user.studentprofile)
    now = timezone.now()

    if reservation.start_time - now < timedelta(hours=1):
        messages.error(request, "Cancellation period has expired. You can no longer cancel this reservation.")
        return redirect('parking:dashboard')

    reservation.status = 'cancelled'
    reservation.save()

    parking_lot = reservation.parking_lot
    parking_lot.available_spots += 1
    parking_lot.save()

    messages.success(request, f"Reservation at {parking_lot.name} cancelled successfully.")
    return redirect('parking:dashboard')
