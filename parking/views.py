from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from urllib.parse import urlencode

import json
import random
import re
import string
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from .forms import StudentLoginForm, StudentSignupForm, VehicleForm
from .models import ParkingLot, Reservation, StudentProfile, Vehicle
from .utils import demo


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _next_reservation_for(student_profile):
    now = timezone.now()
    return (
        Reservation.objects.filter(
            student=student_profile,
            end_time__gt=now,  # Use __gt instead of __gte to exclude reservations that just ended
            status__in=["confirmed", "pending", "active"]
        )
        .order_by("start_time")
        .first()
    )


def _hero_locations() -> list[dict[str, Any]]:
    return [
        {
            "slug": "aub",
            "name": _("AUB Campus"),
            "status_kind": "reserved",
            "status_label": _("Reserved"),
            "eta": _("10 min"),
            "availability_label": _("12 open · 3 full"),
            "availability": [{"state": "open", "label": _("Open")} for _idx in range(4)]
            + [{"state": "busy", "label": _("High demand")} for _idx in range(2)],
            "featured_lot": _("Gemmayze Skyline Hub"),
            "hint": _("Access code ready • Gate opens on arrival"),
            "arrival": "18:20",
            "exit": "20:00",
        },
        {
            "slug": "seaside",
            "name": _("Seaside Promenade"),
            "status_kind": "flow",
            "status_label": _("Live flow"),
            "eta": _("6 min"),
            "availability_label": _("8 open · 1 full"),
            "availability": [{"state": "open", "label": _("Open")} for _idx in range(5)]
            + [{"state": "busy", "label": _("High demand")}],
            "featured_lot": _("Sunrise Deck Garage"),
            "hint": _("License plate reader enabled • EV bays free"),
            "arrival": "08:45",
            "exit": "11:15",
        },
        {
            "slug": "hamra",
            "name": _("Hamra Culture Hub"),
            "status_kind": "wait",
            "status_label": _("Short wait"),
            "eta": _("14 min"),
            "availability_label": _("5 open · 4 holding"),
            "availability": [{"state": "open", "label": _("Open")} for _idx in range(3)]
            + [{"state": "busy", "label": _("High demand")} for _idx in range(3)],
            "featured_lot": _("Rue Bliss Courtyard"),
            "hint": _("Valet assist active • Height limit 2.1m"),
            "arrival": "19:10",
            "exit": "21:00",
        },
    ]


def home(request):
    Reservation.auto_refresh_statuses()

    stats = []
    for stat in demo.hero_stats():
        stats.append(
            {
                "label": stat.label,
                "value": stat.value,
                "suffix": stat.suffix,
                "prefill": "0",
            }
        )

    locations = _hero_locations()
    hero_location = locations[0]

    next_reservation = None
    upcoming_reservations = []
    if request.user.is_authenticated:
        student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
        next_reservation = _next_reservation_for(student_profile)
        now = timezone.now()
        upcoming_reservations = list(
            Reservation.objects.filter(
                student=student_profile,
                status__in=["confirmed", "pending", "active"],
                end_time__gt=now,  # Use __gt to exclude reservations that have ended
            ).order_by("start_time")[:3]
        )

    context = {
        "features": demo.feature_trio(),
        "stats": stats,
        "testimonials": demo.testimonials(),
        "hero_locations": locations,
        "hero_location": hero_location,
        "next_reservation": next_reservation,
        "upcoming_reservations": upcoming_reservations,
    }
    return render(request, "home.html", context)


@require_GET
def home_reservation_card(request):
    Reservation.auto_refresh_statuses()

    reservations = []
    if request.user.is_authenticated:
        student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
        now = timezone.now()
        reservations = list(
            Reservation.objects.filter(
                student=student_profile,
                status__in=["confirmed", "pending", "active"],
                end_time__gt=now,  # Use __gt to exclude reservations that have ended
            ).order_by("start_time")[:3]
        )

    html = render_to_string(
        "partials/_home_reservation_card.html",
        {"reservations": reservations},
        request=request,
    )
    return HttpResponse(html)


def signup(request):
    if request.method == "POST":
        form = StudentSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            verification_code = "".join(random.choices(string.digits, k=6))
            profile = user.studentprofile
            profile.verification_code = verification_code
            profile.save()
            messages.success(request, _("Account created successfully! Please verify your email."))
            return redirect("parking:verify_email")
    else:
        form = StudentSignupForm()
    return render(
        request,
        "auth/signup.html",
        {
            "form": form,
            "HTML_CLASS": "auth-shell",
            "IS_AUTH_PAGE": True,
            "feature_points": [
                _("Keep your reservations in sync across devices."),
                _("Download receipts instantly after each stay."),
                _("Switch languages with one tap — fully RTL ready."),
            ],
        },
    )


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
    if request.method == "POST":
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            credential = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = None
            if "@" in credential:
                try:
                    user = User.objects.get(email__iexact=credential)
                except User.DoesNotExist:
                    pass
            else:
                normalized = re.sub(r"\D", "", credential)
                lookup = normalized or credential
                profile = (
                    StudentProfile.objects.filter(phone_number__in=[lookup, credential])
                    .select_related("user")
                    .first()
                )
                if profile:
                    user = profile.user
            if user:
                authenticated_user = authenticate(username=user.username, password=password)
                if authenticated_user:
                    profile = authenticated_user.studentprofile
                    if not profile.email_verified:
                        messages.error(request, _("Please verify your email before logging in."))
                        return redirect("parking:verify_email")
                    login(request, authenticated_user)
                    messages.success(request, _("Logged in successfully!"))
                    return redirect("parking:dashboard")
                else:
                    messages.error(request, _("Invalid credentials."))
            else:
                messages.error(request, _("User not found."))
    else:
        form = StudentLoginForm()
    return render(
        request,
        "auth/login.html",
        {
            "form": form,
            "HTML_CLASS": "auth-shell",
            "IS_AUTH_PAGE": True,
            "feature_points": [
                _("Resume bookings and live availability dashboards."),
                _("Access QR passes and vehicle preferences in seconds."),
                _("Security-first with CSRF protection and smart alerts."),
            ],
        },
    )


@login_required
def dashboard(request):
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    vehicles = student_profile.vehicles.all()
    Reservation.auto_refresh_statuses()
    recent_reservations = Reservation.objects.filter(student=student_profile).order_by('-created_at')

    # Check if user is a parking lot owner
    is_parking_lot_owner = ParkingLot.objects.filter(owner=request.user).exists()
    
    # If owner, get their parking lots and calculate real metrics
    if is_parking_lot_owner:
        owned_lots = ParkingLot.objects.filter(owner=request.user)
        # Calculate real metrics for owner
        from django.db.models import Count, Sum, Q
        
        today = timezone.now().date()
        today_bookings = Reservation.objects.filter(
            parking_lot__in=owned_lots,
            created_at__date=today
        ).count()
        
        total_spots = owned_lots.aggregate(total=Sum('total_spots'))['total'] or 0
        available_spots = owned_lots.aggregate(total=Sum('available_spots'))['total'] or 0
        occupancy = int((total_spots - available_spots) / total_spots * 100) if total_spots > 0 else 0
        
        today_revenue = Reservation.objects.filter(
            parking_lot__in=owned_lots,
            created_at__date=today,
            status__in=['confirmed', 'active', 'completed']
        ).aggregate(total=Sum('total_cost'))['total'] or 0
        
        now = timezone.now()
        live_reservations = Reservation.objects.filter(
            parking_lot__in=owned_lots,
            status__in=['active', 'confirmed'],
            end_time__gt=now  # Use __gt to exclude reservations that have ended
        ).select_related('student__user', 'parking_lot').order_by('-start_time')[:10]
        
        owner_metrics = {
            "cards": [
                {
                    "title": "Today's Bookings",
                    "value": today_bookings,
                    "delta": "+12%",  # You can calculate this dynamically later
                },
                {
                    "title": "Occupancy",
                    "value": occupancy,
                    "unit": "%",
                    "delta": "+5%",
                },
                {
                    "title": "Revenue",
                    "value": float(today_revenue),
                    "unit": "USD",
                    "delta": "+18%",
                },
            ],
            "table_rows": [
                {
                    "lot": res.parking_lot.name,
                    "driver": res.student.user.get_full_name() or res.student.user.username,
                    "check_in": res.start_time.strftime("%H:%M"),
                    "status": res.status.title(),
                }
                for res in live_reservations
            ],
            "reserved": demo.dashboard_metrics().get("reserved"),  # Keep the demo reserved card for now
        }
    else:
        owner_metrics = None
        live_reservations = None

    context = {
        "student": student_profile,
        "vehicles": vehicles,
        "recent_reservations": recent_reservations[:6],
        "metrics": owner_metrics if is_parking_lot_owner else demo.dashboard_metrics(),
        "is_parking_lot_owner": is_parking_lot_owner,
        "live_reservations": live_reservations,
    }
    return render(request, "dashboard.html", context)



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


def find_parking(request):
    query = request.GET.get("q", request.GET.get("query", "")).strip()
    active_filter = request.GET.get("filter", "all")
    current_sort = request.GET.get("sort", "closest")
    live_enabled = request.GET.get("live") in {"1", "true", "on"}

    raw_lots = demo.demo_lots()

    def prepare_lot(item: dict[str, Any]) -> dict[str, Any]:
        tags = item.get("tags") or []
        if not tags:
            tags = ["🛡️ 24/7 secure", "⚡ Instant access"]
        else:
            tags = [tag if tag.strip().startswith(("🛡", "⚡", "🚗", "🔌", "🅿")) else f"• {tag}" for tag in tags]
        return {
            "id": item.get("id"),
            "name": item.get("name") or item.get("title", "Parking lot"),
            "address": item.get("address", ""),
            "open": item.get("available") or item.get("open") or 0,
            "capacity": item.get("total") or item.get("capacity") or 0,
            "price": item.get("price") or item.get("rate") or item.get("hourly_rate"),
            "distance_km": item.get("distance") or item.get("distance_km") or 0,
            "tags": tags,
        }

    lots = [prepare_lot(item) for item in raw_lots]

    if query:
        q = query.lower()
        lots = [
            lot
            for lot in lots
            if q in lot["name"].lower() or q in lot["address"].lower()
        ]

    filter_sort_map = {
        "closest": lambda lot: lot["distance_km"],
        "best_price": lambda lot: lot["price"] if lot["price"] is not None else float("inf"),
        "availability": lambda lot: (-lot["open"], lot["capacity"]),
    }

    if active_filter in filter_sort_map:
        key_fn = filter_sort_map[active_filter]
        reverse = active_filter == "availability"
        lots = sorted(lots, key=key_fn, reverse=reverse)

    sort_map = {
        "closest": lambda lot: lot["distance_km"],
        "price_asc": lambda lot: lot["price"] if lot["price"] is not None else float("inf"),
        "price_desc": lambda lot: lot["price"] if lot["price"] is not None else float("-inf"),
        "availability_desc": lambda lot: lot["open"],
    }

    if current_sort in sort_map:
        reverse = current_sort in {"price_desc", "availability_desc"}
        lots = sorted(lots, key=sort_map[current_sort], reverse=reverse)

    lots_json = json.dumps(raw_lots, cls=DjangoJSONEncoder)

    context = {
        "query": query,
        "lots": lots,
        "lots_json": lots_json,
        "active_filter": active_filter,
        "current_sort": current_sort,
        "live_enabled": live_enabled,
        "show_skeletons": False,
        "next_url": "",
        "empty_animation": static("img/lottie/search-empty.json"),
    }

    if is_htmx(request):
        html = render_to_string("partials/_results_items.html", context, request=request)
        response = HttpResponse(html)
        response["HX-Trigger"] = json.dumps({"map:update": {"lots": raw_lots}})
        return response

    return render(request, "find_parking.html", context)


def parking_lot_detail(request, parking_lot_id):
    lot_data = None
    try:
        lot_obj = ParkingLot.objects.get(pk=parking_lot_id)
        lot_data = {
            "id": lot_obj.id,
            "title": lot_obj.name,
            "address": lot_obj.address,
            "available": lot_obj.available_spots,
            "total": lot_obj.total_spots,
            "rate": float(lot_obj.hourly_rate),
            "distance": 0.6,
            "latitude": float(lot_obj.latitude),
            "longitude": float(lot_obj.longitude),
            "ev_chargers": 6,
            "height_limit": "2.1m",
        }
    except ParkingLot.DoesNotExist:
        for lot in demo.demo_lots():
            if int(lot["id"]) == parking_lot_id:
                lot_data = {
                    **lot,
                    "ev_chargers": 4,
                    "height_limit": "2.2m",
                }
                break

    if not lot_data:
        return redirect("parking:find_parking")

    lot_data.setdefault("banner", static("img/textures/lot-banner.svg"))
    lot_data.setdefault("amenities", ["License plate reader", "EV ready", "Valet assist", "Rain-sheltered"])

    context = {
        "lot": lot_data,
        "timeline": demo.availability_timeline(),
    }
    return render(request, "lot_detail.html", context)


def reserve_partial(request, parking_lot_id):
    lot_obj = ParkingLot.objects.filter(pk=parking_lot_id).first()
    simulation_only = False
    if not lot_obj:
        demo_lot = next((lot for lot in demo.demo_lots() if int(lot["id"]) == parking_lot_id), None)
        if not demo_lot:
            return HttpResponse(status=404)
        simulation_only = True
        lot_context = demo_lot
    else:
        lot_context = {
            "id": lot_obj.id,
            "title": lot_obj.name,
            "rate": float(lot_obj.hourly_rate),
        }

    if not request.user.is_authenticated:
        current_url = request.headers.get("HX-Current-URL") or request.META.get("HTTP_REFERER") or reverse("parking:find_parking")
        params = urlencode({"next": current_url})
        context = {
            "lot": lot_context,
            "login_url": f"{reverse('parking:login')}?{params}",
            "signup_url": reverse('parking:signup'),
        }
        html = render_to_string("partials/_auth_gate_modal.html", context, request=request)
        return HttpResponse(html)

    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    vehicles = list(student_profile.vehicles.all())
    vehicle_warning = False
    if not vehicles:
        vehicle_warning = True

    now = timezone.now()
    active_reservations_qs = Reservation.objects.filter(
        student=student_profile,
        status__in=["confirmed", "pending", "active"],
        end_time__gt=now,  # Use __gt to exclude reservations that have ended
    )
    max_reservations = 3
    active_reservations_count = active_reservations_qs.count()
    max_reservations_reached = not simulation_only and active_reservations_count >= max_reservations
    latest_reservation = active_reservations_qs.order_by("-end_time").first()

    if request.method == "POST":
        if max_reservations_reached:
            html = render_to_string(
                "partials/_reserve_modal.html",
                {
                    "lot": lot_context,
                    "vehicles": vehicles,
                    "error": _("You already have %(count)d active reservations. Cancel one to book another.")
                    % {"count": active_reservations_count},
                    "default_start": request.POST.get("start_time") or "",
                    "default_end": request.POST.get("end_time") or "",
                    "vehicle_warning": vehicle_warning,
                    "max_reservations_reached": True,
                    "max_reservations": max_reservations,
                    "active_reservations_count": active_reservations_count,
                },
                request=request,
            )
            return HttpResponse(html, status=422)

        vehicle_id = request.POST.get("vehicle")
        start_time_str = request.POST.get("start_time")
        end_time_str = request.POST.get("end_time")

        if not vehicle_id or not start_time_str or not end_time_str:
            html = render_to_string(
                "partials/_reserve_modal.html",
                {
                    "lot": lot_context,
                    "vehicles": vehicles,
                    "error": _("All fields are required."),
                    "default_start": start_time_str,
                    "default_end": end_time_str,
                    "vehicle_warning": vehicle_warning,
                    "max_reservations_reached": max_reservations_reached,
                    "max_reservations": max_reservations,
                    "active_reservations_count": active_reservations_count,
                },
                request=request,
            )
            return HttpResponse(html, status=422)

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M"), tz)
        end_dt = timezone.make_aware(datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M"), tz)

        if end_dt <= start_dt:
            html = render_to_string(
                "partials/_reserve_modal.html",
                {
                    "lot": lot_context,
                    "vehicles": vehicles,
                    "error": _("End time must be after start time."),
                    "default_start": start_time_str,
                    "default_end": end_time_str,
                    "vehicle_warning": vehicle_warning,
                    "max_reservations_reached": max_reservations_reached,
                    "max_reservations": max_reservations,
                    "active_reservations_count": active_reservations_count,
                },
                request=request,
            )
            return HttpResponse(html, status=422)

        if simulation_only:
            start_local = timezone.localtime(start_dt)
            end_local = timezone.localtime(end_dt)
            html = render_to_string(
                "partials/_reservation_success_modal.html",
                {
                    "simulation_only": True,
                    "reservation": None,
                    "lot": lot_context,
                    "start_time": start_local,
                    "end_time": end_local,
                    "vehicle": None,
                },
                request=request,
            )
            response = HttpResponse(html)
            payload = {
                "title": _("Reservation simulated"),
                "message": _("Your demo reservation for %(lot)s is confirmed.") % {"lot": lot_context["title"]},
                "variant": "success",
            }
            response["X-UniPark-Toast"] = json.dumps(payload)
            response["HX-Trigger"] = json.dumps({"reservation:refresh": {}})
            return response

        vehicle = get_object_or_404(Vehicle, id=vehicle_id, student=student_profile)
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        total_cost = Decimal(duration_hours) * lot_obj.hourly_rate

        reservation = Reservation.objects.create(
            student=student_profile,
            vehicle=vehicle,
            parking_lot=lot_obj,
            start_time=start_dt,
            end_time=end_dt,
            total_cost=total_cost,
            status="confirmed",
        )
        reservation.generate_qr_code()
        reservation.save()
        lot_obj.available_spots = max(lot_obj.available_spots - 1, 0)
        lot_obj.save()

        start_local = timezone.localtime(start_dt)
        end_local = timezone.localtime(end_dt)
        html = render_to_string(
            "partials/_reservation_success_modal.html",
            {
                "simulation_only": False,
                "reservation": reservation,
                "lot": lot_context,
                "start_time": start_local,
                "end_time": end_local,
                "vehicle": vehicle,
            },
            request=request,
        )
        response = HttpResponse(html)
        payload = {
            "title": _("Reservation confirmed"),
            "message": _("You're booked from %(start)s to %(end)s.") % {
                "start": timezone.localtime(start_dt).strftime("%H:%M"),
                "end": timezone.localtime(end_dt).strftime("%H:%M"),
            },
            "variant": "success",
        }
        response["X-UniPark-Toast"] = json.dumps(payload)
        trigger_payload = {"reservation:refresh": {"id": reservation.id}}
        response["HX-Trigger"] = json.dumps(trigger_payload)
        return response

    default_start = timezone.localtime().replace(minute=0, second=0, microsecond=0) + timedelta(minutes=30)
    if latest_reservation:
        latest_end_local = timezone.localtime(latest_reservation.end_time)
        if latest_end_local > default_start:
            default_start = latest_end_local + timedelta(minutes=30)
    default_end = default_start + timedelta(hours=2)

    context = {
        "lot": lot_context,
        "vehicles": vehicles,
        "default_start": default_start.strftime("%Y-%m-%dT%H:%M"),
        "default_end": default_end.strftime("%Y-%m-%dT%H:%M"),
        "vehicle_warning": vehicle_warning,
        "max_reservations_reached": max_reservations_reached,
        "max_reservations": max_reservations,
        "active_reservations_count": active_reservations_count,
    }
    html = render_to_string("partials/_reserve_modal.html", context, request=request)
    return HttpResponse(html)


@login_required
def settings_view(request):
    student_profile = request.user.studentprofile
    primary_vehicle = student_profile.vehicles.filter(is_primary=True).first()
    primary_label = _("Not set")
    if primary_vehicle:
        primary_label = f"{primary_vehicle.make} {primary_vehicle.model} · {primary_vehicle.license_plate}"

    context = {
        "primary_vehicle": primary_label,
        "shortcuts": demo.settings_shortcuts(),
    }
    return render(request, "settings.html", context)


def toggle_language(request):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("parking:home")
    current = translation.get_language() or settings.LANGUAGE_CODE
    new_lang = "ar" if current.startswith("en") else "en"
    translation.activate(new_lang)
    session_key = getattr(translation, "LANGUAGE_SESSION_KEY", "django_language")
    request.session[session_key] = new_lang
    response = redirect(next_url)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, new_lang, max_age=60 * 60 * 24 * 365, samesite="Lax")
    response.set_cookie("unipark_theme_direction", new_lang, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response


@require_GET
def hero_location(request):
    slug = request.GET.get("location")
    locations = _hero_locations()
    location = next((item for item in locations if item["slug"] == slug), locations[0])
    html = render_to_string("partials/_hero_card.html", {"location": location}, request=request)
    return HttpResponse(html)



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

    if request.method != "POST":
        messages.error(request, _("Please use the cancel button to request a cancellation."))
        return redirect("parking:dashboard")

    now = timezone.now()

    if reservation.start_time - now < timedelta(hours=1):
        if is_htmx(request):
            response = HttpResponse("", status=422)
            response["HX-Reswap"] = "none"
            response["X-UniPark-Toast"] = json.dumps(
                {
                    "title": _("Too late to cancel"),
                    "message": _("Cancellations are only allowed up to 1 hour before start."),
                    "variant": "warning",
                }
            )
            return response
        messages.error(request, _("Cancellation period has expired. You can no longer cancel this reservation."))
        return redirect("parking:dashboard")

    reservation.status = "cancelled"
    reservation.save()

    parking_lot = reservation.parking_lot
    parking_lot.available_spots = min(parking_lot.available_spots + 1, parking_lot.total_spots)
    parking_lot.save()

    payload = {
        "title": _("Reservation cancelled"),
        "message": _("Your spot at %(lot)s is now released.") % {"lot": parking_lot.name},
        "variant": "info",
    }

    if is_htmx(request):
        response = HttpResponse("", status=204)
        response["HX-Reswap"] = "none"
        response["X-UniPark-Toast"] = json.dumps(payload)
        response["HX-Trigger"] = json.dumps({"reservation:refresh": {}})
        return response

    messages.success(request, _("Reservation at %(lot)s cancelled successfully.") % {"lot": parking_lot.name})
    return redirect("parking:dashboard")


@login_required
def check_in(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if reservation.checked_in:
        messages.info(request, "You’ve already checked in.")
    else:
        reservation.checked_in = True
        reservation.save()
        messages.success(request, f"Checked in successfully for {reservation.parking_lot.name}!")
    return redirect('parking:dashboard')
