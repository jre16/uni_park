from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI(title="API Gateway", version="1.0")

# Service URLs
AUTH_SERVICE = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
PARKING_SERVICE = os.getenv("PARKING_SERVICE_URL", "http://parking-service:8002")
RESERVATIONS_SERVICE = os.getenv("RESERVATIONS_SERVICE_URL", "http://reservations-service:8003")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="/app/static"), name="static")
app.mount("/media", StaticFiles(directory="/app/media"), name="media")
templates = Jinja2Templates(directory="/app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "api-gateway"}

# Auth proxy routes
@app.post("/api/auth/register")
async def register(request: Request):
    """Proxy to auth service"""
    async with httpx.AsyncClient() as client:
        body = await request.json()
        response = await client.post(f"{AUTH_SERVICE}/register", json=body)
        return response.json()

@app.post("/api/auth/token")
async def login(request: Request):
    """Proxy to auth service"""
    async with httpx.AsyncClient() as client:
        form_data = await request.form()
        response = await client.post(
            f"{AUTH_SERVICE}/token",
            data=form_data
        )
        return response.json()

@app.post("/api/auth/verify-email")
async def verify_email(request: Request):
    """Proxy to auth service"""
    async with httpx.AsyncClient() as client:
        body = await request.json()
        response = await client.post(f"{AUTH_SERVICE}/verify-email", json=body)
        return response.json()

@app.get("/api/auth/me")
async def get_current_user(request: Request):
    """Proxy to auth service"""
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTH_SERVICE}/me",
            headers={"Authorization": token}
        )
        return response.json()

# Parking proxy routes
@app.get("/api/parking/lots")
async def get_lots():
    """Proxy to parking service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PARKING_SERVICE}/lots")
        return response.json()

@app.get("/api/parking/lots/{lot_id}")
async def get_lot(lot_id: int):
    """Proxy to parking service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PARKING_SERVICE}/lots/{lot_id}")
        return response.json()

@app.post("/api/parking/lots/nearby")
async def get_nearby_lots(request: Request):
    """Proxy to parking service"""
    async with httpx.AsyncClient() as client:
        body = await request.json()
        response = await client.post(f"{PARKING_SERVICE}/lots/nearby", json=body)
        return response.json()

@app.post("/api/parking/vehicles")
async def create_vehicle(request: Request):
    """Proxy to parking service"""
    async with httpx.AsyncClient() as client:
        body = await request.json()
        response = await client.post(f"{PARKING_SERVICE}/vehicles", json=body)
        return response.json()

@app.get("/api/parking/vehicles/student/{student_id}")
async def get_student_vehicles(student_id: int):
    """Proxy to parking service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{PARKING_SERVICE}/vehicles/student/{student_id}")
        return response.json()

# Reservations proxy routes
@app.post("/api/reservations")
async def create_reservation(request: Request):
    """Proxy to reservations service"""
    async with httpx.AsyncClient() as client:
        body = await request.json()
        response = await client.post(f"{RESERVATIONS_SERVICE}/reservations", json=body)
        return response.json()

@app.get("/api/reservations/student/{student_id}")
async def get_student_reservations(student_id: int):
    """Proxy to reservations service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RESERVATIONS_SERVICE}/reservations/student/{student_id}")
        return response.json()

@app.get("/api/reservations/{reservation_id}")
async def get_reservation(reservation_id: int):
    """Proxy to reservations service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{RESERVATIONS_SERVICE}/reservations/{reservation_id}")
        return response.json()

@app.post("/api/reservations/{reservation_id}/checkin")
async def check_in(reservation_id: int):
    """Proxy to reservations service"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{RESERVATIONS_SERVICE}/reservations/{reservation_id}/checkin")
        return response.json()

@app.post("/api/reservations/{reservation_id}/cancel")
async def cancel_reservation(reservation_id: int, request: Request):
    """Proxy to reservations service"""
    async with httpx.AsyncClient() as client:
        body = await request.json()
        response = await client.post(f"{RESERVATIONS_SERVICE}/reservations/{reservation_id}/cancel", json=body)
        return response.json()

# Frontend routes
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/find", response_class=HTMLResponse)
async def find_parking(request: Request):
    return templates.TemplateResponse("find_parking.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("auth/signup.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
