from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, Time, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from datetime import time as time_type
import os
import re

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres-parking:5432/parking_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Parking Service", version="1.0")

# Models
class ParkingLot(Base):
    __tablename__ = "parking_lots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    owner_id = Column(Integer, nullable=True)
    address = Column(Text)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    hourly_rate = Column(Numeric(6, 2))
    daily_rate = Column(Numeric(6, 2))
    monthly_rate = Column(Numeric(8, 2))
    total_spots = Column(Integer)
    available_spots = Column(Integer)
    opening_time = Column(Time)
    closing_time = Column(Time)
    features = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, index=True)
    make = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    license_plate = Column(String(20), unique=True)
    color = Column(String(30), nullable=True)
    is_primary = Column(Boolean, default=False)

# Pydantic models
class ParkingLotCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    hourly_rate: float
    daily_rate: float
    monthly_rate: float
    total_spots: int
    available_spots: int
    opening_time: str  # "HH:MM"
    closing_time: str  # "HH:MM"
    features: Optional[str] = None
    owner_id: Optional[int] = None

class ParkingLotResponse(BaseModel):
    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    hourly_rate: float
    daily_rate: float
    monthly_rate: float
    total_spots: int
    available_spots: int
    opening_time: str
    closing_time: str
    features: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

class VehicleCreate(BaseModel):
    student_id: int
    make: str
    model: str
    year: int
    license_plate: str
    color: Optional[str] = None
    is_primary: bool = False

class VehicleResponse(BaseModel):
    id: int
    student_id: int
    make: str
    model: str
    year: int
    license_plate: str
    color: Optional[str]
    is_primary: bool
    
    class Config:
        from_attributes = True

class NearbyRequest(BaseModel):
    latitude: float
    longitude: float
    radius: float = 5.0

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def validate_license_plate(plate: str) -> str:
    """Validate and format Lebanese license plate"""
    formatted_plate = re.sub(r'\s+', '', plate.upper().strip())
    match = re.fullmatch(r'([A-Z])(\d{2,8})', formatted_plate or '')
    if not match:
        raise HTTPException(status_code=400, detail="Invalid Lebanese license plate format. Use format like: B 123456")
    return f"{match.group(1)} {match.group(2)}"

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points"""
    from math import radians, sin, cos, asin, sqrt
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c

# Routes
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"service": "parking", "status": "running"}

@app.post("/lots", response_model=ParkingLotResponse, status_code=status.HTTP_201_CREATED)
def create_lot(lot: ParkingLotCreate, db: Session = Depends(get_db)):
    db_lot = ParkingLot(**lot.dict())
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot

@app.get("/lots", response_model=List[ParkingLotResponse])
def get_lots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    lots = db.query(ParkingLot).filter(ParkingLot.is_active == True).offset(skip).limit(limit).all()
    return lots

@app.get("/lots/{lot_id}", response_model=ParkingLotResponse)
def get_lot(lot_id: int, db: Session = Depends(get_db)):
    lot = db.query(ParkingLot).filter(ParkingLot.id == lot_id).first()
    if not lot:
        raise HTTPException(status_code=404, detail="Parking lot not found")
    return lot

@app.post("/lots/nearby", response_model=List[ParkingLotResponse])
def get_nearby_lots(request: NearbyRequest, db: Session = Depends(get_db)):
    lots = db.query(ParkingLot).filter(ParkingLot.is_active == True).all()
    nearby = []
    for lot in lots:
        distance = haversine(request.latitude, request.longitude, float(lot.latitude), float(lot.longitude))
        if distance <= request.radius:
            nearby.append(lot)
    return nearby

@app.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    # Validate license plate
    vehicle.license_plate = validate_license_plate(vehicle.license_plate)
    
    # Check if plate already exists
    existing = db.query(Vehicle).filter(Vehicle.license_plate == vehicle.license_plate).first()
    if existing:
        raise HTTPException(status_code=400, detail="License plate already registered")
    
    # If marking as primary, unset other primaries for this student
    if vehicle.is_primary:
        db.query(Vehicle).filter(Vehicle.student_id == vehicle.student_id).update({"is_primary": False})
    
    db_vehicle = Vehicle(**vehicle.dict())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@app.get("/vehicles/student/{student_id}", response_model=List[VehicleResponse])
def get_student_vehicles(student_id: int, db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).filter(Vehicle.student_id == student_id).all()
    return vehicles

@app.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@app.delete("/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.commit()
    return {"message": "Vehicle deleted"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
