from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import random
import string
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres-auth:5432/auth_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Auth Service", version="1.0")

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    phone_number = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    phone: str = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class VerifyEmail(BaseModel):
    email: EmailStr
    code: str

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Routes
@app.on_event("startup")
def startup():
    logger.info("🚀 Auth Service starting up...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")
    logger.info("✅ Auth Service ready on port 8001")

@app.get("/")
def root():
    return {"service": "auth", "status": "running"}

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"=== REGISTRATION STARTED ===")
    logger.info(f"Username: {user.username}")
    logger.info(f"Email: {user.email}")
    
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logger.warning(f"Registration failed: Email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        logger.warning(f"Registration failed: Username {user.username} already taken")
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"✅ User created with ID: {db_user.id}")
    
    # Create profile
    verification_code = ''.join(random.choices(string.digits, k=6))
    profile = StudentProfile(
        user_id=db_user.id,
        phone_number=user.phone,
        verification_code=verification_code
    )
    db.add(profile)
    db.commit()
    
    logger.info(f"=" * 60)
    logger.info(f"🔑 VERIFICATION CODE FOR {user.email}: {verification_code}")
    logger.info(f"=" * 60)
    logger.info(f"✅ Registration completed successfully for {user.username}")
    
    return db_user

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"=== LOGIN ATTEMPT ===")
    logger.info(f"Username: {form_data.username}")
    
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"❌ Login failed: Incorrect credentials for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check email verification
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile and not profile.email_verified:
        logger.warning(f"❌ Login failed: Email not verified for {form_data.username}")
        raise HTTPException(status_code=403, detail="Please verify your email first")
    
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"✅ Login successful for {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/verify-email")
def verify_email(data: VerifyEmail, db: Session = Depends(get_db)):
    logger.info(f"=== EMAIL VERIFICATION ATTEMPT ===")
    logger.info(f"Email: {data.email}")
    logger.info(f"Code provided: {data.code}")
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        logger.warning(f"❌ Verification failed: User not found for {data.email}")
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        logger.warning(f"❌ Verification failed: Profile not found for {data.email}")
        raise HTTPException(status_code=404, detail="Profile not found")
    
    logger.info(f"Expected code: {profile.verification_code}")
    
    if profile.verification_code != data.code:
        logger.warning(f"❌ Verification failed: Invalid code for {data.email}")
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    profile.email_verified = True
    profile.verification_code = None
    db.commit()
    
    logger.info(f"✅ Email verified successfully for {data.email}")
    return {"message": "Email verified successfully"}

@app.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
