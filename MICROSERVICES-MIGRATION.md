# UNIPARK 2.0: Monolith to Microservices Migration

## Overview

This document explains the transformation of UNIPARK 2.0 from a Django monolithic application to a microservices architecture deployed on Kubernetes (Minikube).

---

## Table of Contents

1. [Original Monolithic Architecture](#original-monolithic-architecture)
2. [Microservices Architecture](#microservices-architecture)
3. [Migration Strategy](#migration-strategy)
4. [Services Breakdown](#services-breakdown)
5. [Database Architecture](#database-architecture)
6. [Deployment Architecture](#deployment-architecture)
7. [Communication Patterns](#communication-patterns)
8. [Benefits & Trade-offs](#benefits--trade-offs)

---

## Original Monolithic Architecture

### Structure

The original UNIPARK 2.0 was a single Django application with the following components:

```
UNIPARK 2.0 (Monolith)
├── Django Application (Single Process)
│   ├── Authentication & User Management
│   ├── Parking Lot Management
│   ├── Vehicle Registration
│   ├── Reservation System
│   ├── QR Code Generation
│   └── Frontend Templates (HTML/CSS/JS)
│
└── SQLite Database (Single File)
    ├── Users & Student Profiles
    ├── Parking Lots
    ├── Vehicles
    └── Reservations
```

### Characteristics

- **Single Codebase**: All functionality in one Django project
- **Single Database**: SQLite file (`db.sqlite3`)
- **Single Deployment Unit**: One server, one process
- **Tight Coupling**: All components depend on each other
- **Scaling**: Must scale entire application together

### Limitations

1. **Scalability**: Can't scale individual features independently
2. **Deployment**: Small change requires redeploying entire app
3. **Technology Lock-in**: Entire app must use Django
4. **Database Bottleneck**: Single database for all operations
5. **Fault Isolation**: One bug can crash entire application

---

## Microservices Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (Minikube)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐         ┌──────────────────┐               │
│  │  Users/Browser  │────────▶│  NodePort 30080  │               │
│  └─────────────────┘         └────────┬─────────┘               │
│                                       │                          │
│                              ┌────────▼────────┐                 │
│                              │ Django Frontend │ (2 replicas)    │
│                              │  Port 8000      │                 │
│                              │ ┌─────────────┐ │                 │
│                              │ │  Templates  │ │                 │
│                              │ │   Views     │ │                 │
│                              │ │  Static Files│ │                 │
│                              │ └─────────────┘ │                 │
│                              └─┬───┬───┬───┬──┘                 │
│                                │   │   │   │                     │
│              ┌─────────────────┘   │   │   └─────────────┐       │
│              │                     │   │                 │       │
│   ┌──────────▼──────────┐ ┌───────▼───────┐ ┌──────────▼─────┐ │
│   │   Auth Service      │ │ Parking Service│ │ Reservations   │ │
│   │   (FastAPI)         │ │   (FastAPI)    │ │   Service      │ │
│   │   Port 8001         │ │   Port 8002    │ │  (FastAPI)     │ │
│   │   (2 replicas)      │ │   (2 replicas) │ │  Port 8003     │ │
│   │                     │ │                │ │  (2 replicas)  │ │
│   │ ┌─────────────────┐ │ │ ┌────────────┐ │ │ ┌────────────┐ │ │
│   │ │ JWT Auth        │ │ │ │ Parking    │ │ │ │ QR Codes   │ │ │
│   │ │ Registration    │ │ │ │ Lots       │ │ │ │ Bookings   │ │ │
│   │ │ Email Verify    │ │ │ │ Vehicles   │ │ │ │ Check-in   │ │ │
│   │ └─────────────────┘ │ │ │ Geolocation│ │ │ │ Status     │ │ │
│   └──────────┬──────────┘ │ └────────────┘ │ │ └────────────┘ │ │
│              │            └────────┬───────┘ └────────┬────────┘ │
│              │                     │                  │          │
│   ┌──────────▼──────────┐ ┌───────▼───────┐ ┌────────▼────────┐ │
│   │ PostgreSQL          │ │ PostgreSQL    │ │ PostgreSQL      │ │
│   │ (auth_db)           │ │ (parking_db)  │ │ (reservations_db│ │
│   │ Port 5432           │ │ Port 5432     │ │ Port 5432)      │ │
│   └─────────────────────┘ └───────────────┘ └─────────────────┘ │
│                                                                   │
│   ┌─────────────────────┐                                        │
│   │ PostgreSQL          │                                        │
│   │ (unipark_db)        │                                        │
│   │ Frontend DB         │                                        │
│   │ Port 5432           │                                        │
│   └─────────────────────┘                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Components

1. **Frontend Service** (Django)
   - Original Django application
   - Serves HTML templates and static files
   - Handles user interface
   - Can communicate with backend microservices via API

2. **Auth Service** (FastAPI)
   - User authentication & registration
   - JWT token generation
   - Email verification
   - Student profile management

3. **Parking Service** (FastAPI)
   - Parking lot CRUD operations
   - Vehicle management
   - Geolocation-based search
   - Lebanese license plate validation

4. **Reservations Service** (FastAPI)
   - Reservation booking
   - QR code generation
   - Check-in/check-out
   - Status management (pending, confirmed, active, completed)

---

## Migration Strategy

### Approach: Strangler Fig Pattern (Modified)

We used a **hybrid approach** that preserves the original Django app while creating new microservices:

```
Phase 1: Containerization
├── Created Dockerfiles for each service
├── Separated concerns into services
└── Maintained Django as primary frontend

Phase 2: Service Decomposition
├── Extracted Auth logic → Auth Service
├── Extracted Parking logic → Parking Service
├── Extracted Reservations logic → Reservations Service
└── Kept Django frontend intact

Phase 3: Database Separation
├── Created separate PostgreSQL instances
├── One database per service (isolation)
└── Frontend keeps its own database

Phase 4: Kubernetes Deployment
├── Created K8s manifests
├── Configured services and networking
├── Set up persistent volumes
└── Deployed to Minikube
```

---

## Services Breakdown

### 1. Django Frontend Service

**Technology**: Django 5.2.7, Gunicorn  
**Port**: 8000  
**Replicas**: 2  
**Database**: PostgreSQL (unipark_db)

**Responsibilities**:
- Serve web interface (HTML templates)
- Handle HTTP requests from users
- Render dynamic pages
- Serve static files (CSS, JS, images)
- Session management
- CSRF protection
- User authentication (Django auth)

**Files**:
```
services/frontend/
├── Dockerfile
└── requirements.txt (Django, gunicorn, psycopg2)
```

**Key Features**:
- Auto-runs migrations on startup
- Loads sample data from fixtures
- Collects static files during build
- Uses original Django templates and views

---

### 2. Auth Service

**Technology**: FastAPI, SQLAlchemy, JWT  
**Port**: 8001  
**Replicas**: 2  
**Database**: PostgreSQL (auth_db)

**Responsibilities**:
- User registration with email/phone
- JWT token generation and validation
- Email verification code generation
- Student profile management
- OAuth2 password flow authentication

**API Endpoints**:
```
POST   /register           - Create new user
POST   /token             - Login & get JWT token
POST   /verify-email      - Verify email with code
GET    /me                - Get current user profile
```

**Database Schema**:
```sql
users
├── id (PK)
├── username
├── email
├── hashed_password
└── created_at

student_profiles
├── id (PK)
├── user_id (FK)
├── phone_number
├── email_verified
├── verification_code
└── created_at
```

**Files**:
```
services/auth/
├── Dockerfile
├── requirements.txt
└── main.py (215 lines)
```

---

### 3. Parking Service

**Technology**: FastAPI, SQLAlchemy  
**Port**: 8002  
**Replicas**: 2  
**Database**: PostgreSQL (parking_db)

**Responsibilities**:
- Parking lot CRUD operations
- Vehicle registration and management
- Geolocation-based search (Haversine formula)
- Lebanese license plate validation
- Availability tracking

**API Endpoints**:
```
GET    /lots              - List all parking lots
GET    /lots/nearby       - Find lots near coordinates
GET    /lots/{id}         - Get specific lot details
POST   /lots              - Create new parking lot
PUT    /lots/{id}         - Update parking lot
DELETE /lots/{id}         - Delete parking lot

GET    /vehicles          - List vehicles (by student)
POST   /vehicles          - Register new vehicle
```

**Database Schema**:
```sql
parking_lots
├── id (PK)
├── name
├── address
├── latitude
├── longitude
├── hourly_rate
├── total_spots
├── available_spots
├── opening_time
└── closing_time

vehicles
├── id (PK)
├── student_id (FK)
├── make
├── model
├── year
├── license_plate (validated format)
└── color
```

**Geolocation Algorithm**:
- Haversine formula for distance calculation
- Radius-based search (default 5km)
- Sorts results by distance

**Files**:
```
services/parking/
├── Dockerfile
├── requirements.txt
└── main.py (227 lines)
```

---

### 4. Reservations Service

**Technology**: FastAPI, SQLAlchemy, QRCode  
**Port**: 8003  
**Replicas**: 2  
**Database**: PostgreSQL (reservations_db)

**Responsibilities**:
- Reservation booking and management
- QR code generation (base64 PNG)
- Check-in/check-out functionality
- Auto-status refresh based on time
- Cost calculation

**API Endpoints**:
```
GET    /reservations              - List all reservations
POST   /reservations              - Create new reservation
GET    /reservations/{id}         - Get specific reservation
POST   /reservations/{id}/checkin - Check in with QR code
POST   /reservations/{id}/cancel  - Cancel reservation
GET    /reservations/refresh      - Auto-refresh statuses
```

**Database Schema**:
```sql
reservations
├── id (PK)
├── student_id (FK)
├── vehicle_id (FK)
├── lot_id (FK)
├── status (pending/confirmed/active/completed/expired/cancelled)
├── start_time
├── end_time
├── total_cost
├── qr_code (base64)
└── created_at
```

**Status State Machine**:
```
pending → confirmed → active → completed
    ↓         ↓         ↓
  cancelled  expired  cancelled
```

**Auto-Refresh Logic**:
- `pending` → `confirmed` when near start time
- `confirmed` → `active` when within start time
- `active` → `completed` when past end time
- `confirmed` → `expired` when missed start time

**Files**:
```
services/reservations/
├── Dockerfile
├── requirements.txt
└── main.py (217 lines)
```

---

## Database Architecture

### Database-per-Service Pattern

Each microservice has its **own independent PostgreSQL database**:

```
┌─────────────────────────────────────────────────────────┐
│                  Database Isolation                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Frontend ──────▶ postgres-frontend:5432/unipark_db      │
│                   ├── Users (Django auth)                │
│                   ├── Student Profiles                   │
│                   ├── Vehicles                           │
│                   ├── Parking Lots                       │
│                   └── Reservations                       │
│                                                           │
│  Auth ──────────▶ postgres-auth:5432/auth_db            │
│                   ├── Users                              │
│                   └── Student Profiles                   │
│                                                           │
│  Parking ───────▶ postgres-parking:5432/parking_db      │
│                   ├── Parking Lots                       │
│                   └── Vehicles                           │
│                                                           │
│  Reservations ──▶ postgres-reservations:5432/reservations_db │
│                   └── Reservations                       │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Why PostgreSQL Instead of SQLite?

**SQLite Issues in Containers**:
- ❌ File-based (lost when container restarts)
- ❌ Can't handle concurrent connections
- ❌ No network access (can't be shared)
- ❌ Not suitable for production

**PostgreSQL Benefits**:
- ✅ Client-server architecture
- ✅ Survives container restarts (persistent volumes)
- ✅ Handles multiple concurrent connections
- ✅ Production-ready and scalable
- ✅ Better performance for microservices

### Persistent Volumes

Each PostgreSQL instance uses a **PersistentVolumeClaim** (500Mi each):

```yaml
postgres-auth-pvc          → /var/lib/postgresql/data (auth_db)
postgres-parking-pvc       → /var/lib/postgresql/data (parking_db)
postgres-reservations-pvc  → /var/lib/postgresql/data (reservations_db)
postgres-frontend-pvc      → /var/lib/postgresql/data (unipark_db)
```

This ensures data persists even when pods are recreated.

---

## Deployment Architecture

### Kubernetes Resources

```
Deployments (8 total):
├── postgres-auth (1 replica)
├── postgres-parking (1 replica)
├── postgres-reservations (1 replica)
├── postgres-frontend (1 replica)
├── auth-service (2 replicas)
├── parking-service (2 replicas)
├── reservations-service (2 replicas)
└── unipark-frontend (2 replicas)

Services (8 total):
├── postgres-auth (ClusterIP, port 5432)
├── postgres-parking (ClusterIP, port 5432)
├── postgres-reservations (ClusterIP, port 5432)
├── postgres-frontend (ClusterIP, port 5432)
├── auth-service (ClusterIP, port 8001)
├── parking-service (ClusterIP, port 8002)
├── reservations-service (ClusterIP, port 8003)
└── unipark-frontend (NodePort 30080, port 8000)

PersistentVolumeClaims (4 total):
├── postgres-auth-pvc (500Mi)
├── postgres-parking-pvc (500Mi)
├── postgres-reservations-pvc (500Mi)
└── postgres-frontend-pvc (500Mi)
```

### Resource Allocation

**Microservices** (Auth, Parking, Reservations):
```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

**Frontend**:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "200m"
  limits:
    memory: "512Mi"
    cpu: "400m"
```

**Databases**:
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "200m"
```

**Total Resources** (with 2 replicas per service):
- **14 Pods** running simultaneously
- **~4GB RAM** total across cluster
- **~2 CPU cores** total allocation

### Networking

**Service Discovery** (DNS-based):
```
auth-service:8001
parking-service:8002
reservations-service:8003
postgres-auth:5432
postgres-parking:5432
postgres-reservations:5432
postgres-frontend:5432
```

**External Access**:
```
NodePort 30080 → unipark-frontend:8000
URL: http://<minikube-ip>:30080
```

---

## Communication Patterns

### Service-to-Service Communication

**Frontend → Backend Services** (Optional):
```python
# parking/microservices_client.py
from typing import Optional, Dict
import requests

class MicroservicesClient:
    def __init__(self):
        self.auth_service = "http://auth-service:8001"
        self.parking_service = "http://parking-service:8002"
        self.reservations_service = "http://reservations-service:8003"
    
    def create_user(self, username, email, password):
        return requests.post(
            f"{self.auth_service}/register",
            json={"username": username, "email": email, "password": password}
        )
```

**Current Architecture**:
- Frontend uses its own database (SQLite/PostgreSQL)
- Backend microservices are **optional** (can be used for future API endpoints)
- Services communicate via HTTP REST APIs
- No message queue (simple synchronous calls)

**Future Enhancement**:
- Add API Gateway pattern
- Implement async messaging (RabbitMQ/Kafka)
- Add service mesh (Istio)
- Implement circuit breakers

---

## Benefits & Trade-offs

### ✅ Benefits

**Scalability**:
- Scale individual services independently
- Add replicas only where needed
- Example: Scale reservations service during peak hours

**Deployment**:
- Deploy services independently
- Update auth service without touching parking service
- Faster release cycles

**Technology Flexibility**:
- Frontend: Django
- Backend: FastAPI (faster, async)
- Can add services in Node.js, Go, etc.

**Fault Isolation**:
- If parking service crashes, auth still works
- Database failures are isolated
- Better resilience

**Development**:
- Teams can work on different services
- Clear boundaries and responsibilities
- Easier to test individual components

**Database**:
- Each service owns its data
- No schema conflicts
- Can optimize database per service needs

### ⚠️ Trade-offs

**Complexity**:
- 14 pods vs 1 monolith
- More configuration (Dockerfiles, K8s manifests)
- Need Kubernetes knowledge

**Data Consistency**:
- No database transactions across services
- Need eventual consistency patterns
- Data duplication possible

**Network Latency**:
- Service-to-service calls add latency
- More network hops
- Need proper error handling

**Debugging**:
- Logs distributed across services
- Need centralized logging (ELK stack)
- Distributed tracing helpful

**Resource Overhead**:
- Each service has overhead (memory, CPU)
- 4 databases vs 1
- More Docker images to manage

**Testing**:
- Integration tests more complex
- Need to test service interactions
- Local development setup more involved

---

## Deployment Process

### One-Command Deployment

```powershell
.\deploy-microservices.ps1
```

**What it does**:
1. ✅ Checks Minikube status
2. ✅ Switches to Minikube Docker environment
3. ✅ Builds 4 Docker images:
   - `unipark-auth:latest`
   - `unipark-parking:latest`
   - `unipark-reservations:latest`
   - `unipark-frontend:latest`
4. ✅ Applies Kubernetes manifests
5. ✅ Waits for deployments to be ready
6. ✅ Shows service URL

### Manual Deployment Steps

```bash
# 1. Start Minikube
minikube start --driver=docker

# 2. Switch to Minikube Docker
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# 3. Build images
docker build -t unipark-auth:latest ./services/auth
docker build -t unipark-parking:latest ./services/parking
docker build -t unipark-reservations:latest ./services/reservations
docker build -t unipark-frontend:latest -f services/frontend/Dockerfile .

# 4. Deploy to Kubernetes
kubectl apply -f k8s/microservices.yaml

# 5. Check status
kubectl get pods
kubectl get svc

# 6. Access application
minikube service unipark-frontend
```

---

## Monitoring & Management

### Check Deployment Status

```bash
# View all pods
kubectl get pods

# View services
kubectl get svc

# View persistent volumes
kubectl get pvc
```

### View Logs

```bash
# Frontend logs
kubectl logs -l app=unipark-frontend

# Auth service logs
kubectl logs -l app=auth-service

# Parking service logs
kubectl logs -l app=parking-service

# Reservations service logs
kubectl logs -l app=reservations-service

# Database logs
kubectl logs -l app=postgres-frontend
```

### Scale Services

```bash
# Scale frontend to 5 replicas
kubectl scale deployment unipark-frontend --replicas=5

# Scale auth service to 3 replicas
kubectl scale deployment auth-service --replicas=3

# Check scaling
kubectl get pods -l app=unipark-frontend
```

### Update Service

```bash
# Rebuild image
docker build -t unipark-frontend:latest -f services/frontend/Dockerfile .

# Restart deployment (picks up new image)
kubectl rollout restart deployment/unipark-frontend

# Check rollout status
kubectl rollout status deployment/unipark-frontend
```

### Debugging

```bash
# Describe pod for events
kubectl describe pod <pod-name>

# Execute command in pod
kubectl exec -it <pod-name> -- /bin/bash

# Port forward to local machine
kubectl port-forward svc/auth-service 8001:8001

# Check resource usage
kubectl top pods
kubectl top nodes
```

---

## File Structure

```
UNIPARK 2.0/
├── services/
│   ├── frontend/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── auth/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   └── .dockerignore
│   ├── parking/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   └── .dockerignore
│   ├── reservations/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   └── .dockerignore
│   └── api_gateway/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── main.py
│       ├── templates/
│       └── .dockerignore
├── k8s/
│   └── microservices.yaml (520+ lines)
├── parking/
│   ├── models.py
│   ├── views.py
│   ├── microservices_client.py
│   └── ...
├── templates/
├── static/
├── deploy-microservices.ps1
├── cleanup-microservices.ps1
├── README-MICROSERVICES.md
└── MICROSERVICES-MIGRATION.md (this file)
```

---

## Conclusion

### What We Achieved

✅ **Transformed** Django monolith into microservices  
✅ **Preserved** original app integrity (UI, templates, views)  
✅ **Deployed** 4 independent services on Kubernetes  
✅ **Implemented** database-per-service pattern  
✅ **Enabled** independent scaling and deployment  
✅ **Created** production-ready architecture  

### Key Takeaways

1. **Hybrid Approach**: Kept Django frontend, extracted backend logic
2. **FastAPI**: Used for microservices (fast, async, modern)
3. **PostgreSQL**: Replaced SQLite for production-readiness
4. **Kubernetes**: Enables orchestration, scaling, resilience
5. **Docker**: Containerization for consistency across environments

### Future Enhancements

- **API Gateway**: Add proper gateway (Kong, Traefik)
- **Service Mesh**: Implement Istio for advanced networking
- **Monitoring**: Add Prometheus + Grafana
- **Logging**: Centralized logging with ELK stack
- **CI/CD**: GitHub Actions for automated deployment
- **Load Testing**: Verify scaling capabilities
- **Security**: Add OAuth2, rate limiting, encryption
- **Message Queue**: Async communication with RabbitMQ/Kafka

---

**Project**: UNIPARK 2.0  
**Course**: EECE 430  
**Institution**: AUB (American University of Beirut)  
**Semester**: Fall 2025  
**Date**: November 2025  

---

*This microservices architecture demonstrates modern cloud-native application design, suitable for scalable, resilient production deployments.*
