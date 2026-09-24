# ScreenHive

## Cinema Seat Booking Backend

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLModel](https://img.shields.io/badge/SQLModel-ORM-4B5563?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Firestore](https://img.shields.io/badge/Firestore-Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)
![JWT](https://img.shields.io/badge/JWT-Authentication-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Paystack](https://img.shields.io/badge/Paystack-Payments-00C3F7?style=for-the-badge)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-6B7280?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-Testing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![Server-Sent Events](https://img.shields.io/badge/SSE-Live_Updates-FF6B35?style=for-the-badge)
![uv](https://img.shields.io/badge/uv-Package_Manager-6E56CF?style=for-the-badge)
 
---

# 1. Project Overview

A cinema seat booking backend built with FastAPI, PostgreSQL, Redis, Firestore, and Docker.

ScreenHive focuses on reliable seat reservations under concurrent traffic, using PostgreSQL transactions and row-level locking to prevent multiple users from successfully holding the same seat.

The system allows users to:

- register and log in
- browse films
- view screens and showtimes
- view available seats
- temporarily hold seats
- create bookings
- initiate payments
- receive payment confirmation through signed webhooks
- receive live showtime updates through Server-Sent Events

The system also includes:

- role-based authentication
- Redis caching
- rate limiting
- request ID and timing middleware
- background tasks
- scheduled hold cleanup
- PostgreSQL transactions
- row-level locking
- idempotent payment webhooks
- automated tests
- Docker
- GitHub Actions CI

The main engineering challenge is the **seat-hold concurrency problem**, also known as the **thundering herd problem**.

The system must guarantee that when multiple users attempt to hold the same seat simultaneously, only one request succeeds.

---

# 2. Core Architectural Principle

PostgreSQL is the **source of truth** for transactional data.

Redis, Firestore, background tasks, and scheduled jobs do not replace PostgreSQL.

```text
                     PostgreSQL
                   SOURCE OF TRUTH
                         |
          +--------------+--------------+
          |              |              |
        Seats          Holds         Bookings
          |              |              |
          +--------------+--------------+
                         |
                      Payments
```

For example, Redis may contain:

```text
A10 = available
```

but that cached value is never treated as authoritative during a seat transaction.

The database determines the actual state.

---

# 3. Architecture

```mermaid
flowchart TD

    U[Users]

    U --> API[FastAPI /api/v1]

    API --> PG[(PostgreSQL)]
    API --> R[(Redis)]
    API --> FS[(Firestore)]

    FS --> SSE[Server-Sent Events]
    SSE --> B[Browser]

    P[Payment Provider] -->|Signed Webhook| API

    J[Scheduled Job] --> PG

    API --> BG[Background Tasks]
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| FastAPI | API layer and request handling |
| PostgreSQL | Source of truth and transactional data |
| Redis | Caching and rate limiting |
| Firestore | Live/stream-shaped data |
| SSE | Delivers live showtime updates |
| Paystack | Payment processing |
| Background tasks | Non-critical asynchronous work |
| Scheduled job | Hold cleanup and housekeeping |
| GitHub Actions | Automated testing |

---

# 4. Application Architecture

ScreenHive follows a layered architecture.

```text
HTTP Request
     |
     v
  Router
     |
     v
  Service
     |
     v
 Database
```

### Routers

Routers are responsible for:

- receiving HTTP requests
- validating input
- calling services
- returning HTTP responses

### Services

Services contain business rules such as:

- seat holding
- booking
- payment processing
- authentication
- pricing
- seat-map caching

### Database

PostgreSQL handles:

- persistent data
- relationships
- foreign keys
- unique constraints
- indexes
- transactions
- row locking

This keeps route functions thin and makes the business logic easier to test.

---

# 5. Project Structure

```text
screenhive/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── rate_limit.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   └── models/
│   │       ├── user.py
│   │       ├── film.py
│   │       ├── screen.py
│   │       ├── showtime.py
│   │       ├── seat_inventory.py
│   │       ├── hold.py
│   │       ├── booking.py
│   │       ├── booking_seat.py
│   │       ├── payment.py
│   │       ├── processed_event.py
│   │       └── price_rule.py
│   │
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   ├── cache/
│   ├── firestore/
│   ├── middleware/
│   ├── tasks/
│   └── jobs/
│
├── tests/
├── scripts/
│   └── seed.py
│
├── alembic/
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .env.example
└── README.md
```

---

# 6. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Programming language |
| FastAPI | Web framework |
| SQLModel | ORM and database models |
| PostgreSQL | Primary database |
| Redis | Cache and rate limiting |
| Firestore | Live stream data |
| JWT | User authentication |
| Argon2 | Password hashing |
| Paystack | Payment processing |
| Alembic | Database migrations |
| Pytest | Automated testing |
| Docker | Containerization |
| GitHub Actions | CI |

---

# 7. Setup Instructions

## Prerequisites

Install:

- Python 3.14+
- Docker
- Docker Compose
- uv
- Git

---

## Clone the project

```bash
git clone <repository-url>
cd screenhive
```

---

## Install dependencies

```bash
uv sync
```

---

## Environment variables

Create a `.env` file based on `.env.example`.

Example:

```env
DATABASE_URL=postgresql+psycopg://screenhive:screenhive_password@localhost:5432/screenhive
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-this-secret
PAYSTACK_SECRET=
FIREBASE_PROJECT_ID=
FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
FIRESTORE_ENABLED=true
```

Never commit `.env` or service-account credentials.

---

# 8. Run with Docker

Start PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

Run database migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

# 9. Run the Complete Docker Stack

The project also provides an API container.

```bash
docker compose up -d --build
```

Check the containers:

```bash
docker compose ps
```

The API should be available at:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 10. Database Migrations

ScreenHive uses Alembic for database migrations.

Apply migrations:

```bash
uv run alembic upgrade head
```

Create a new migration:

```bash
uv run alembic revision --autogenerate -m "describe change"
```

Check the current migration:

```bash
uv run alembic current
```

---

# 11. Seed Data

The project includes a seed script for demo data.

Run:

```bash
uv run python -m scripts.seed
```

When using the Docker API container:

```bash
docker compose exec api uv run python -m scripts.seed
```

The seed script creates:

- demo users
- films
- screens
- showtimes
- seats
- a sample pricing rule

The seed script is designed to be safe to run repeatedly without creating additional demo showtimes.

---

# 12. Demo Accounts

The seed script creates three demo roles.

| Role | Email | Password |
|---|---|---|
| Moviegoer | `moviegoer@screenhive.com` | `password123` |
| Cashier | `cashier@screenhive.com` | `password123` |
| Manager | `manager@screenhive.com` | `password123` |

These accounts are for local/demo use only.

Production credentials must be different.

---

# 13. Authentication

ScreenHive uses **JWT authentication** for human users.

Passwords are hashed using Argon2 through `pwdlib`.

The authentication flow is:

```text
User
 |
 | email + password
 v
Login Endpoint
 |
 v
Verify Password
 |
 v
Generate JWT
 |
 v
Client
 |
 | Authorization: Bearer <token>
 v
Protected Endpoint
 |
 v
Get Current User
 |
 v
Role / Ownership Checks
```

## Roles

ScreenHive currently supports:

- `moviegoer`
- `cashier`
- `manager`

Authentication failures return `401`.

Authenticated users without sufficient permissions receive `403`.

Ownership checks are performed in the relevant services.

---

# 14. Machine Authentication

Payment webhooks do not use user login.

The payment provider calls the webhook endpoint using a signed request.

The webhook signature is verified using the configured payment secret.

This separates:

```text
Human users
    |
    v
JWT authentication
```

from:

```text
Machine caller
    |
    v
Signed webhook
```

A machine caller should never be given a human login account just to access a webhook.

---

# 15. ERD

```mermaid
erDiagram

    USER ||--o{ HOLD : creates
    USER ||--o{ BOOKING : creates

    FILM ||--o{ SHOWTIME : has
    SCREEN ||--o{ SHOWTIME : hosts

    SHOWTIME ||--o{ SEAT_INVENTORY : contains

    SEAT_INVENTORY ||--o{ HOLD : has

    BOOKING ||--o{ BOOKING_SEAT : contains
    SEAT_INVENTORY ||--o{ BOOKING_SEAT : reserved

    BOOKING ||--o{ PAYMENT : has

    FILM ||--o{ PRICE_RULE : has

    USER {
        int id PK
        string email
        string password_hash
        string full_name
        string role
    }

    FILM {
        int id PK
        string title
        string description
        int duration_minutes
        string rating
        float base_price
    }

    SCREEN {
        int id PK
        string name
        int total_seats
    }

    SHOWTIME {
        int id PK
        int film_id FK
        int screen_id FK
        datetime start_time
        datetime end_time
        float ticket_price
    }

    SEAT_INVENTORY {
        int id PK
        int showtime_id FK
        string seat_number
        string status
    }

    HOLD {
        int id PK
        int user_id FK
        int seat_inventory_id FK
        string status
        datetime expires_at
    }

    BOOKING {
        int id PK
        int user_id FK
        int showtime_id FK
        string reference
        string status
        float total_amount
    }

    PAYMENT {
        int id PK
        int booking_id FK
        string reference
        string status
    }
```

---

# 16. Seat Lifecycle

```text
AVAILABLE
    |
    | Successful hold
    v
  HELD
   / \
  /   \
payment expires
 |       |
 v       v
BOOKED  AVAILABLE
```

A hold contains an `expires_at` timestamp.

The expiration time is checked during relevant transactions.

The scheduled job is responsible for cleanup and housekeeping. It is not the authority for determining whether a hold was valid at the exact moment of a transaction.

---

# 17. The Thundering Herd Drill

The most important concurrency problem in ScreenHive is preventing two users from successfully holding the same seat.

Example:

```text
User A                    User B
   |                         |
   | Hold seat A10           | Hold seat A10
   |                         |
   +------------+------------+
                |
                v
          Hold Service
                |
                v
       BEGIN TRANSACTION
                |
                v
     SELECT seat FOR UPDATE
                |
                v
          User A proceeds
          User B waits
                |
                v
             HELD
                |
                v
             COMMIT
                |
                v
          User B resumes
                |
                v
          Seat already held
                |
                v
          409 CONFLICT
```

The critical protection is the PostgreSQL row lock:

```python
.with_for_update()
```

This prevents concurrent requests from both successfully modifying the same seat.

---

# 18. Drill Guarantees

The test suite covers:

1. Two users attempting the same seat.
2. Five users attempting the same seat.
3. Losing requests receiving a conflict.
4. Different seats being held concurrently.
5. An expired hold being reclaimed under contention.

The expected result is that only one request can successfully hold a particular seat at a time.

---

# 19. Redis Cache

Redis is used as a cache.

The main cached resource is the **showtime seat map**.

```text
Request
   |
   v
Redis
   |
   +---- Cache hit ---> Return seat map
   |
   +---- Cache miss
              |
              v
          PostgreSQL
              |
              v
        Store in Redis
```

The cache has a short expiration period.

When seat state changes:

```text
Database Change
      |
      v
Invalidate Redis
      |
      v
Next request reads fresh data
```

Redis is never treated as the source of truth.

---

# 20. Rate Limiting

Redis is also used for rate limiting.

The login endpoint is protected against repeated requests.

When the limit is exceeded, the API returns:

```text
429 Too Many Requests
```

with a:

```text
Retry-After
```

header.

---

# 21. Firestore Boundary

Firestore has a deliberately narrow responsibility.

It is used for **stream-shaped/live data**, not core transactional booking data.

```text
PostgreSQL
    |
    | Transactional state
    v
Seats / Holds / Bookings / Payments
```

while:

```text
Firestore
    |
    | Live showtime board
    v
SSE
    |
    v
Browser
```

The live showtime board can contain information such as:

- available seats
- held seats
- booked seats
- showtime information

PostgreSQL remains the authority for the actual seat state.

---

# 22. Server-Sent Events

ScreenHive exposes a Server-Sent Events stream for live showtime information.

The flow is:

```text
PostgreSQL
     |
     v
Application
     |
     v
Firestore Live Board
     |
     v
SSE Endpoint
     |
     v
Browser
```

This allows clients to receive live updates without repeatedly requesting the entire resource.

---

# 23. Payment Webhooks

Payment completion is handled through a signed webhook.

The flow is:

```text
Payment Provider
       |
       | Signed webhook
       v
FastAPI
       |
       v
Verify Signature
       |
       v
Find Payment
       |
       v
Process Payment
       |
       v
Update Booking
       |
       v
Update Seat
       |
       v
Update Hold
       |
       v
Commit PostgreSQL Transaction
       |
       v
Invalidate Cache
       |
       v
Publish Live Update
```

Webhook processing is idempotent.

Processed webhook events are stored so that the same event cannot be processed twice.

---

# 24. Pricing

ScreenHive supports dynamic pricing through price rules.

The pricing service:

1. checks active pricing rules
2. selects the highest-priority applicable rule
3. falls back to the film's base price when no rule applies

This keeps pricing logic inside the service layer rather than inside route functions.

---

# 25. Scheduled Hold Cleanup

ScreenHive includes a scheduled job that checks for expired holds.

The job:

- finds expired active holds
- marks them as expired
- releases their seats
- invalidates the relevant Redis seat-map cache
- updates the live showtime board

However, the scheduled job is **not the authority for hold validity**.

A booking/payment transaction checks:

```text
expires_at
+
transaction
+
row locking
```

This prevents correctness from depending on whether the scheduler happened to run at exactly the right second.

---

# 26. Request Middleware

Each request receives:

```text
X-Request-ID
```

and:

```text
X-Process-Time
```

Example:

```text
X-Request-ID: <uuid>
X-Process-Time: 0.0124
```

This helps with request tracing and basic performance visibility.

---

# 27. Testing

ScreenHive uses Pytest with a separate PostgreSQL test database.

The test suite covers:

- authentication
- invalid credentials
- authorization
- ownership
- films
- screens
- showtimes
- holds
- bookings
- payments
- payment webhooks
- cache behavior
- rate limiting
- scheduled hold expiry
- pricing
- concurrency
- conflict responses

The project has more than 25 automated tests, including the five concurrency drill scenarios.

Run the tests locally:

```bash
uv run pytest
```

---

# 28. Continuous Integration

GitHub Actions runs the test suite on:

- pushes
- pull requests

The CI environment starts:

- PostgreSQL
- Redis

and then runs:

```bash
uv sync
uv run pytest
```

Firestore is disabled in CI because the test suite does not require a live Firebase project.

---

# 29. Docker

The project provides:

```text
Dockerfile
docker-compose.yml
```

Docker Compose runs:

```text
API
PostgreSQL
Redis
```

Start everything:

```bash
docker compose up -d --build
```

Check services:

```bash
docker compose ps
```

View API logs:

```bash
docker compose logs api
```

Stop the stack:

```bash
docker compose down
```

---

# 30. API Documentation

FastAPI automatically provides interactive Swagger documentation.

Local documentation:

```text
http://localhost:8000/docs
```

OpenAPI schema:

```text
http://localhost:8000/openapi.json
```

The API is organized under:

```text
/api/v1
```

---

# 31. Main API Areas

```text
/api/v1/auth
/api/v1/films
/api/v1/screens
/api/v1/showtimes
/api/v1/seatmap
/api/v1/holds
/api/v1/bookings
/api/v1/payments
/api/v1/webhooks
/api/v1/stream
```

Swagger UI should be used to test the complete request/response flow before deployment.

---

# 32. Deployment

**Status: Pending**

The application has not yet been deployed.

The planned production architecture is:

```text
                  Internet
                     |
                     v
              FastAPI Application
                     |
          +----------+----------+
          |          |          |
          v          v          v
     PostgreSQL    Redis    Firestore
```

The production deployment will use:

- managed PostgreSQL
- Redis
- environment-based secrets
- Firebase/Firestore configuration
- payment webhook configuration
- database migrations
- seeded demo data where appropriate

### Deployment URL

```text
TBD
```

The live URL will be added after deployment and verification.

---

# 33. Environment Variables

Production secrets must be supplied through the deployment platform.

Required configuration includes:

```env
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
PAYSTACK_SECRET=
FIREBASE_PROJECT_ID=
FIREBASE_CREDENTIALS_PATH=
FIRESTORE_ENABLED=
```

Secrets must never be committed to Git.

---

# 34. Known Limitations

### 1. In-process scheduler

The scheduled hold cleanup currently runs inside the FastAPI application process.

For a horizontally scaled production system, the scheduled job should be moved to a dedicated worker or external scheduler so that multiple API instances do not independently run the same job.

### 2. No frontend

ScreenHive currently focuses on the backend API.

The interactive client is represented through Swagger UI and the SSE endpoint.

### 3. Firestore configuration

Live Firestore functionality requires valid Firebase credentials and configuration.

Local Docker development disables Firestore by default.

### 4. Demo credentials

The seed accounts use simple demo passwords and must never be reused in production.

### 5. Payment provider dependency

Actual payment completion depends on the external payment provider and correctly configured webhook credentials.

---

# 35. Important Design Decisions

### PostgreSQL is the source of truth

Transactional seat state must always come from PostgreSQL.

### Redis is cache only

A stale Redis value must never override database state.

### Firestore is for live data

Firestore is intentionally separated from transactional booking operations.

### Row locking protects seat ownership

Concurrent seat requests use database row locking to prevent double booking.

### Hold expiration is transactionally checked

The scheduler performs cleanup but does not determine whether a hold was valid during a booking/payment transaction.

### Webhooks are machine authenticated

Payment providers authenticate through signed webhooks rather than human JWT login.

### Services contain business logic

Routes remain thin while business rules live in service modules.

---

# 36. Development Philosophy

The project was developed using:

```text
Design
   ↓
Understand
   ↓
Implement
   ↓
Test
   ↓
Document
```

The goal was not only to make the API work, but to understand why each architectural decision exists.

---

# 37. Current Project Status

```text
Project structure              ✓
FastAPI                        ✓
SQLModel                       ✓
PostgreSQL                     ✓
Alembic migrations             ✓
JWT authentication             ✓
Role-based authorization       ✓
Films                          ✓
Screens                        ✓
Showtimes                      ✓
Seat inventory                 ✓
Seat holds                     ✓
Booking                        ✓
Payments                       ✓
Payment webhooks               ✓
Webhook idempotency            ✓
Dynamic pricing                ✓
Redis caching                  ✓
Rate limiting                  ✓
Request middleware             ✓
Firestore live board           ✓
Server-Sent Events             ✓
Scheduled hold cleanup         ✓
Concurrency drill              ✓
Automated tests                ✓
Docker                         ✓
Docker Compose                 ✓
Seed script                    ✓
GitHub Actions CI              ✓
README                         ✓
Deployment                     → Pending
Final Swagger endpoint audit   → Pending
```

---

# 38. Final Verification Checklist

Before deployment:

- [x] Run complete Pytest suite
- [x] Run Alembic migrations against a fresh database
- [x] Run seed script
- [x] Start Docker stack
- [x] Verify PostgreSQL
- [x] Verify Redis
- [x] Verify API
- [x] Test all Swagger endpoints
- [x] Test authentication
- [x] Test role permissions
- [x] Test seat holding
- [x] Test booking
- [x] Test payment flow
- [x] Test webhook
- [x] Test cache invalidation
- [x] Test rate limiting
- [x] Test SSE
- [x] Verify CI
- [x] Review `.env.example`
- [x] Review `.gitignore`
- [x] Verify production `/docs`