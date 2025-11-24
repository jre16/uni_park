from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import os
import qrcode
from io import BytesIO
import base64

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres-reservations:5432/reservations_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Reservations Service", version="1.0")

# Models
class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, index=True)
    vehicle_id = Column(Integer)
    parking_lot_id = Column(Integer)
    status = Column(String(20), default='pending')  # pending, confirmed, active, completed, expired, cancelled
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    total_cost = Column(Numeric(8, 2))
    qr_code = Column(Text, nullable=True)  # base64 encoded
    checked_in = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class ReservationCreate(BaseModel):
    student_id: int
    vehicle_id: int
    parking_lot_id: int
    start_time: datetime
    end_time: datetime
    hourly_rate: float

class ReservationResponse(BaseModel):
    id: int
    student_id: int
    vehicle_id: int
    parking_lot_id: int
    status: str
    start_time: datetime
    end_time: datetime
    total_cost: float
    qr_code: Optional[str]
    checked_in: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def generate_qr_code(reservation_id: int) -> str:
    """Generate QR code as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(f"http://unipark.app/checkin/{reservation_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()

def auto_refresh_statuses(db: Session):
    """Automatically update reservation statuses based on time"""
    now = datetime.utcnow()
    
    # Promote to active
    db.query(Reservation).filter(
        Reservation.status.in_(['pending', 'confirmed']),
        Reservation.start_time <= now,
        Reservation.end_time > now
    ).update({"status": "active"}, synchronize_session=False)
    
    # Mark as completed if checked in
    db.query(Reservation).filter(
        Reservation.status.in_(['pending', 'confirmed', 'active']),
        Reservation.end_time <= now,
        Reservation.checked_in == True
    ).update({"status": "completed"}, synchronize_session=False)
    
    # Mark as expired if not checked in
    db.query(Reservation).filter(
        Reservation.status.in_(['pending', 'confirmed', 'active']),
        Reservation.end_time <= now,
        Reservation.checked_in == False
    ).update({"status": "expired"}, synchronize_session=False)
    
    db.commit()

# Routes
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"service": "reservations", "status": "running"}

@app.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db)):
    # Calculate cost
    duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
    total_cost = Decimal(str(duration_hours)) * Decimal(str(reservation.hourly_rate))
    
    # Create reservation
    db_reservation = Reservation(
        student_id=reservation.student_id,
        vehicle_id=reservation.vehicle_id,
        parking_lot_id=reservation.parking_lot_id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        total_cost=total_cost,
        status='confirmed'
    )
    db.add(db_reservation)
    db.commit()
    db.refresh(db_reservation)
    
    # Generate QR code
    qr_code = generate_qr_code(db_reservation.id)
    db_reservation.qr_code = qr_code
    db.commit()
    db.refresh(db_reservation)
    
    return db_reservation

@app.get("/reservations/student/{student_id}", response_model=List[ReservationResponse])
def get_student_reservations(student_id: int, db: Session = Depends(get_db)):
    auto_refresh_statuses(db)
    reservations = db.query(Reservation).filter(Reservation.student_id == student_id).order_by(Reservation.created_at.desc()).all()
    return reservations

@app.get("/reservations/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation

@app.post("/reservations/{reservation_id}/checkin")
def check_in(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if reservation.checked_in:
        return {"message": "Already checked in"}
    
    reservation.checked_in = True
    reservation.status = 'active'
    db.commit()
    
    return {"message": "Checked in successfully"}

@app.post("/reservations/{reservation_id}/cancel")
def cancel_reservation(reservation_id: int, student_id: int, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.student_id == student_id
    ).first()
    
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Check if cancellation is allowed (at least 1 hour before)
    now = datetime.utcnow()
    if reservation.start_time - now < timedelta(hours=1):
        raise HTTPException(status_code=400, detail="Too late to cancel. Cancellations must be made at least 1 hour before start time")
    
    reservation.status = 'cancelled'
    db.commit()
    
    return {"message": "Reservation cancelled successfully"}

@app.get("/reservations/active/count")
def get_active_count(student_id: int, db: Session = Depends(get_db)):
    auto_refresh_statuses(db)
    count = db.query(Reservation).filter(
        Reservation.student_id == student_id,
        Reservation.status.in_(['pending', 'confirmed', 'active'])
    ).count()
    return {"count": count}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
