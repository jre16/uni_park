"""
Microservices client for UNIPARK backend services
"""
import os
import requests
from typing import Optional, Dict, Any

class MicroservicesClient:
    """Client to communicate with backend microservices"""
    
    def __init__(self):
        self.auth_service = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
        self.parking_service = os.getenv("PARKING_SERVICE_URL", "http://parking-service:8002")
        self.reservations_service = os.getenv("RESERVATIONS_SERVICE_URL", "http://reservations-service:8003")
        self.timeout = 5
    
    def _request(self, method: str, url: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """Make HTTP request to microservice"""
        try:
            kwargs.setdefault('timeout', self.timeout)
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Microservice request failed: {e}")
            return None
    
    # Auth Service Methods
    def create_user(self, username: str, email: str, password: str, phone: str = None) -> Optional[Dict]:
        """Create user in auth service"""
        return self._request('POST', f"{self.auth_service}/register", json={
            "username": username,
            "email": email,
            "password": password,
            "phone_number": phone
        })
    
    def verify_user(self, user_id: int, code: str) -> Optional[Dict]:
        """Verify user email"""
        return self._request('POST', f"{self.auth_service}/verify-email", json={
            "user_id": user_id,
            "code": code
        })
    
    # Parking Service Methods
    def get_parking_lots(self, lat: float = None, lng: float = None, radius: float = 5.0) -> Optional[list]:
        """Get parking lots, optionally nearby a location"""
        if lat and lng:
            result = self._request('GET', f"{self.parking_service}/lots/nearby", params={
                "lat": lat,
                "lng": lng,
                "radius_km": radius
            })
            return result if result else []
        else:
            result = self._request('GET', f"{self.parking_service}/lots")
            return result if result else []
    
    def get_parking_lot(self, lot_id: int) -> Optional[Dict]:
        """Get single parking lot details"""
        return self._request('GET', f"{self.parking_service}/lots/{lot_id}")
    
    def create_vehicle(self, student_id: int, make: str, model: str, year: int, 
                      license_plate: str, color: str = None) -> Optional[Dict]:
        """Create vehicle"""
        return self._request('POST', f"{self.parking_service}/vehicles", json={
            "student_id": student_id,
            "make": make,
            "model": model,
            "year": year,
            "license_plate": license_plate,
            "color": color
        })
    
    def get_vehicles(self, student_id: int) -> Optional[list]:
        """Get vehicles for a student"""
        result = self._request('GET', f"{self.parking_service}/vehicles", params={
            "student_id": student_id
        })
        return result if result else []
    
    # Reservations Service Methods
    def create_reservation(self, student_id: int, vehicle_id: int, lot_id: int,
                          start_time: str, end_time: str) -> Optional[Dict]:
        """Create parking reservation"""
        return self._request('POST', f"{self.reservations_service}/reservations", json={
            "student_id": student_id,
            "vehicle_id": vehicle_id,
            "lot_id": lot_id,
            "start_time": start_time,
            "end_time": end_time
        })
    
    def get_reservations(self, student_id: int = None, status: str = None) -> Optional[list]:
        """Get reservations"""
        params = {}
        if student_id:
            params['student_id'] = student_id
        if status:
            params['status'] = status
        result = self._request('GET', f"{self.reservations_service}/reservations", params=params)
        return result if result else []
    
    def get_reservation(self, reservation_id: int) -> Optional[Dict]:
        """Get single reservation"""
        return self._request('GET', f"{self.reservations_service}/reservations/{reservation_id}")
    
    def check_in_reservation(self, reservation_id: int, qr_code: str) -> Optional[Dict]:
        """Check in to reservation"""
        return self._request('POST', f"{self.reservations_service}/reservations/{reservation_id}/checkin", json={
            "qr_code": qr_code
        })
    
    def cancel_reservation(self, reservation_id: int) -> Optional[Dict]:
        """Cancel reservation"""
        return self._request('POST', f"{self.reservations_service}/reservations/{reservation_id}/cancel")


# Global microservices client instance
microservices = MicroservicesClient()
