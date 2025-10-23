#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unipark.settings')
django.setup()

from parking.models import ParkingLot
from datetime import time

def create_sample_parking_lots():
    """Create sample parking lot data for AUB area"""
    
    parking_lots = [
        {
            'name': 'AUB Main Gate Parking',
            'address': 'Bliss Street, Hamra, Beirut',
            'latitude': 33.8994,
            'longitude': 35.4839,
            'hourly_rate': 2.00,
            'daily_rate': 15.00,
            'monthly_rate': 200.00,
            'total_spots': 150,
            'available_spots': 45,
            'opening_time': time(6, 0),
            'closing_time': time(23, 0),
            'features': 'Covered parking, Security cameras, Student discount',
        },
        {
            'name': 'Hamra Street Parking',
            'address': 'Hamra Street, Beirut',
            'latitude': 33.8948,
            'longitude': 35.4833,
            'hourly_rate': 3.00,
            'daily_rate': 20.00,
            'monthly_rate': 250.00,
            'total_spots': 80,
            'available_spots': 12,
            'opening_time': time(5, 0),
            'closing_time': time(1, 0),
            'features': '24/7 access, Valet service, EV charging',
        },
        {
            'name': 'AUB Medical Center Parking',
            'address': 'Clemenceau Street, Beirut',
            'latitude': 33.8972,
            'longitude': 35.4856,
            'hourly_rate': 2.50,
            'daily_rate': 18.00,
            'monthly_rate': 220.00,
            'total_spots': 120,
            'available_spots': 67,
            'opening_time': time(0, 0),
            'closing_time': time(23, 59),
            'features': '24/7 access, Handicap accessible, Security',
        },
        {
            'name': 'Ras Beirut Parking Garage',
            'address': 'Ras Beirut, AUB Area',
            'latitude': 33.9012,
            'longitude': 35.4798,
            'hourly_rate': 1.50,
            'daily_rate': 12.00,
            'monthly_rate': 180.00,
            'total_spots': 200,
            'available_spots': 89,
            'opening_time': time(6, 0),
            'closing_time': time(22, 0),
            'features': 'Student discount, Covered parking, Monthly rates',
        },
        {
            'name': 'Corniche Parking Plaza',
            'address': 'Corniche El Manara, Beirut',
            'latitude': 33.8934,
            'longitude': 35.4778,
            'hourly_rate': 4.00,
            'daily_rate': 25.00,
            'monthly_rate': 300.00,
            'total_spots': 100,
            'available_spots': 23,
            'opening_time': time(5, 0),
            'closing_time': time(2, 0),
            'features': 'Sea view, Premium location, Valet service',
        },
        {
            'name': 'AUB Student Center Parking',
            'address': 'AUB Campus, Bliss Street',
            'latitude': 33.8989,
            'longitude': 35.4844,
            'hourly_rate': 1.00,
            'daily_rate': 8.00,
            'monthly_rate': 120.00,
            'total_spots': 300,
            'available_spots': 156,
            'opening_time': time(6, 0),
            'closing_time': time(23, 0),
            'features': 'Student discount, Campus security, Easy access',
        },
        {
            'name': 'Verdun Parking Complex',
            'address': 'Verdun Street, Beirut',
            'latitude': 33.8889,
            'longitude': 35.4889,
            'hourly_rate': 3.50,
            'daily_rate': 22.00,
            'monthly_rate': 280.00,
            'total_spots': 150,
            'available_spots': 34,
            'opening_time': time(0, 0),
            'closing_time': time(23, 59),
            'features': 'Shopping district, 24/7 access, Premium service',
        },
        {
            'name': 'AUB Engineering Parking',
            'address': 'AUB Engineering Complex',
            'latitude': 33.9001,
            'longitude': 35.4823,
            'hourly_rate': 1.25,
            'daily_rate': 10.00,
            'monthly_rate': 140.00,
            'total_spots': 180,
            'available_spots': 78,
            'opening_time': time(6, 0),
            'closing_time': time(23, 0),
            'features': 'Student discount, Engineering building access',
        }
    ]
    
    print("Creating sample parking lots...")
    
    for lot_data in parking_lots:
        lot, created = ParkingLot.objects.get_or_create(
            name=lot_data['name'],
            defaults=lot_data
        )
        
        if created:
            print(f"[+] Created: {lot.name}")
        else:
            print(f"[!] Already exists: {lot.name}")
    
    print(f"\nSample data creation complete! Created {len(parking_lots)} parking lots.")

if __name__ == '__main__':
    create_sample_parking_lots()