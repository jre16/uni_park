"""
Demo content helpers used to populate the premium UI when real data is absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, List

from django.utils import timezone

from ..models import ParkingLot, Reservation


@dataclass
class DemoStat:
    label: str
    value: int | float
    suffix: str = ""


def _now() -> datetime:
    return timezone.now()


def feature_trio() -> list[dict[str, Any]]:
    return [
        {
            "icon": "map-pin",
            "title": "Nearby",
            "description": "Smart recommendations surface the closest lots with real-time availability.",
        },
        {
            "icon": "qr-code",
            "title": "QR Entry",
            "description": "Skip the kiosk. Tap your phone or scan the QR to glide through the gate.",
        },
        {
            "icon": "wallet",
            "title": "Easy Payments",
            "description": "Secure Apple Pay, cards, and campus wallet with automatic receipts.",
        },
    ]


def hero_stats() -> list[DemoStat]:
    lots = ParkingLot.objects.count()
    reservations = Reservation.objects.filter(status="confirmed").count()
    minutes_saved = max(reservations * 7, 180)
    return [
        DemoStat(label="Partner Garages", value=max(lots, 12)),
        DemoStat(label="Happy Drivers", value=max(reservations * 3, 2480), suffix="+"),
        DemoStat(label="Minutes Saved", value=minutes_saved, suffix="k"),
    ]


def testimonials() -> list[dict[str, Any]]:
    return [
        {
            "quote": "UNIPARK honestly changed my life. No more driving around hoping for an empty parking spot.",
            "name": "Layla K.",
            "role": "Architecture Student",
            "avatar": "https://i.pravatar.cc/120?img=47",
        },
        {
            "quote": "I actually arrive to my classes on time now. No stress, no chaos, just park and go.",
            "name": "Omar D.",
            "role": "Graduate Researcher",
            "avatar": "https://i.pravatar.cc/120?img=55",
        },
        {
            "quote": "Honestly… wow. Booking a spot takes seconds. It's way easier than I expected.",
            "name": "Maya S.",
            "role": "Design Lead",
            "avatar": "https://i.pravatar.cc/120?img=15",
        },
    ]


def demo_lots() -> list[dict[str, Any]]:
    lots = list(
        ParkingLot.objects.filter(is_active=True).values(
            "id",
            "name",
            "address",
            "available_spots",
            "total_spots",
            "hourly_rate",
            "latitude",
            "longitude",
        )
    )
    if lots:
        normalised: list[dict[str, Any]] = []
        for item in lots:
            normalised.append(
                {
                    "id": item["id"],
                    "title": item["name"],
                    "address": item["address"],
                    "available": item["available_spots"],
                    "total": item["total_spots"],
                    "rate": float(item["hourly_rate"]),
                    "distance": 0.4,
                    "latitude": float(item["latitude"]) if item["latitude"] else 33.8938,
                    "longitude": float(item["longitude"]) if item["longitude"] else 35.5018,
                    "tags": ["covered", "24/7", "security"],
                }
            )
        return normalised

    # Fallback demo data
    return [
        {
            "id": 101,
            "title": "Gemmayze Skyline Hub",
            "address": "Mar Mikhael, Gouraud Street",
            "available": 28,
            "total": 40,
            "rate": 3.5,
            "distance": 0.4,
            "latitude": 33.8961,
            "longitude": 35.5052,
            "tags": ["covered", "EV ready", "security"],
        },
        {
            "id": 102,
            "title": "Seaside Promenade Deck",
            "address": "Ain El Mreisseh, Beirut Corniche",
            "available": 12,
            "total": 24,
            "rate": 4.0,
            "distance": 0.9,
            "latitude": 33.9021,
            "longitude": 35.4964,
            "tags": ["valet", "seaside"],
        },
        {
            "id": 103,
            "title": "Hamra Culture Garage",
            "address": "Hamra Main Street",
            "available": 2,
            "total": 60,
            "rate": 2.8,
            "distance": 1.2,
            "latitude": 33.8967,
            "longitude": 35.4822,
            "tags": ["membership", "camera"],
        },
    ]


def availability_timeline() -> list[dict[str, Any]]:
    start = _now().replace(minute=0, second=0, microsecond=0)
    blocks: list[dict[str, Any]] = []
    for idx in range(12):
        slot_start = start + timedelta(minutes=30 * idx)
        available = 12 - (idx % 5)
        fill = int((available / 12) * 100)
        blocks.append(
            {
                "time": slot_start.strftime("%H:%M"),
                "available": available,
                "fill": fill,
                "is_peak": idx in {4, 5, 6},
            }
        )
    return blocks


def dashboard_metrics() -> dict[str, Any]:
    now = _now()
    return {
        "cards": [
            {
                "title": "Today's Bookings",
                "value": 68,
                "delta": "+12%",
                "sparkline": [6, 9, 7, 12, 14, 17, 13, 19],
            },
            {
                "title": "Occupancy",
                "value": 82,
                "unit": "%",
                "delta": "+5%",
                "sparkline": [40, 52, 60, 68, 70, 72, 82, 79],
            },
            {
                "title": "Revenue",
                "value": 984,
                "unit": "USD",
                "delta": "+18%",
                "sparkline": [80, 120, 140, 180, 160, 210, 240, 300],
            },
        ],
        "feature_cards": [
            {
                "title": "Nearby Parking",
                "description": "Pinpoint the closest premium garages with occupancy, distance, and walking time in seconds.",
                "icon": """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 21C12 21 5 13.833 5 9.5C5 6.462 7.462 4 10.5 4C12.241 4 13.823 4.83 14.812 6.188C15.801 7.547 16.001 9.348 15.337 10.898C14.5 12.862 12 16 12 16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="10.5" cy="8.5" r="1.6" stroke="currentColor" stroke-width="1.4"/>
    <path d="M12 16L13.5 13.5L17 15" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""".strip(),
            },
            {
                "title": "QR Entry",
                "description": "Wave your phone once. Our adaptive QR unlock syncs directly with gate hardware and driver profiles.",
                "icon": """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="4" y="4" width="6" height="6" rx="1.4" stroke="currentColor" stroke-width="1.5"/>
    <rect x="14" y="4" width="6" height="6" rx="1.4" stroke="currentColor" stroke-width="1.5"/>
    <rect x="4" y="14" width="6" height="6" rx="1.4" stroke="currentColor" stroke-width="1.5"/>
    <path d="M14 14H17V17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M20 14V20H16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
</svg>
""".strip(),
            },
            {
                "title": "Easy Payments",
                "description": "Auto-charge, mint receipts, and sync financials to your ERP without leaving the UniPark dashboard.",
                "icon": """
<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="3.5" y="6" width="17" height="12" rx="2.2" stroke="currentColor" stroke-width="1.5"/>
    <path d="M3.5 10H20.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M15.5 15H16.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M12.5 15H13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
</svg>
""".strip(),
            },
        ],
        "reserved": {
            "title": "Skyline Executive Pod",
            "subtitle": "Your VIP bay is illuminated and ready on level P3.",
            "lot": "Gemmayze Skyline Hub",
            "spot": "Bay 18 · EV",
            "window": f"{(now + timedelta(minutes=15)).strftime('%H:%M')} – {(now + timedelta(hours=2)).strftime('%H:%M')}",
        },
        "table_rows": [
            {
                "lot": "Gemmayze Skyline Hub",
                "check_in": (now - timedelta(minutes=15)).strftime("%H:%M"),
                "driver": "Sami N.",
                "status": "Checked in",
            },
            {
                "lot": "Seaside Promenade Deck",
                "check_in": (now + timedelta(minutes=30)).strftime("%H:%M"),
                "driver": "Hiba F.",
                "status": "Upcoming",
            },
            {
                "lot": "Hamra Culture Garage",
                "check_in": (now - timedelta(hours=1)).strftime("%H:%M"),
                "driver": "Noah R.",
                "status": "Completed",
            },
            {
                "lot": "AUB Medical Center",
                "check_in": (now + timedelta(hours=2)).strftime("%H:%M"),
                "driver": "Dana Y.",
                "status": "Reserved",
            },
        ],
    }


def settings_shortcuts() -> list[dict[str, Any]]:
    return [
        {"label": "Light Theme", "key": "theme", "value": "light"},
        {"label": "Dark Theme", "key": "theme", "value": "dark"},
        {"label": "Increase Font Size", "key": "font", "value": "large"},
        {"label": "High Contrast", "key": "contrast", "value": "high"},
    ]

