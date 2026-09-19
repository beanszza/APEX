<div align="center">

# APEX

**A**nalytical **P**latform for **E**nterprise e**X**cellence

[![Status](https://img.shields.io/badge/status-under%20development-yellow)](https://github.com/beanszza/APEX)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An AI-powered supply chain analytics and intelligence engine for SCMS.

</div>

---

## Overview

APEX is a standalone Python microservice that provides **predictive analytics**, **dashboard intelligence**, and **ML-driven recommendations** for the Supply Chain Management System (SCMS). It runs alongside the existing `api-scms` backend, reading operational data from PostgreSQL and persisting computed analytics in the dedicated `analytics_documents` table in PostgreSQL (`scm_db`), with fast in-memory caching.

| Capability | Description | Tech |
|------------|-------------|------|
| **Dashboard Analytics** | KPIs, inventory charts, procurement trends, production yield | Pandas, NumPy |
| **Demand Forecasting** | Predict monthly usage per item using historical data | Scikit-learn (Linear Regression) |
| **Reorder Optimization** | Recommend reorder quantities based on stock levels + predicted demand | Scikit-learn, NumPy |
| **Production Recommendations** | Suggest batch counts and output quantities per recipe | Scikit-learn (Random Forest) |
| **Low Stock Alerting** | Detect and classify stock alerts (WARNING / CRITICAL) | Pandas |

## Architecture

APEX extracts data from the SCMS PostgreSQL database (`scm_db`), runs predictive and analytics pipelines, and persists compiled documents into the `analytics_documents` table in the same PostgreSQL database, accompanied by in-memory caching.

```
┌─────────────────────────────────────────────────────────┐
│                    R3B2P Ecosystem                       │
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐ │
│  │  host-app    │   │  web-scms    │   │ api-gateway  │ │
│  │  :3000       │   │  :3004       │   │ :5001        │ │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘ │
│         │                  │                   │         │
│         │      ┌───────────┴───────────┐       │         │
│         │      │                       │       │         │
│  ┌──────▼──────▼──┐   ┌───────────────▼──┐    │         │
│  │ ms-auth  :5007 │   │ api-scms  :5006  │    │         │
│  │ (JWT issuer)   │   │ (SCM CRUD)       │    │         │
│  └────────────────┘   └────────┬─────────┘    │         │
│                                │               │         │
│                       ┌────────▼─────────┐     │         │
│                       │   PostgreSQL     │     │         │
│                       │   scm_db         │     │         │
│                       └────────┬─────────┘     │         │
│                                │ READ/WRITE    │         │
│                                │ (analytics)   │         │
│                       ┌────────▼─────────┐     │         │
│                       │   APEX   :5011   │◄────┘         │
│                       │   (Python AI)    │               │
│                       └──────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### How APEX Connects to Other Services

| Connection | Direction | Method | Purpose |
|------------|-----------|--------|---------|
| APEX → PostgreSQL (`scm_db`) | **Read + Write** | SQLAlchemy | Read operational data; save compiled analytics into `analytics_documents` |
| api-gateway → APEX | **Inbound HTTP** | YARP route `/api/scms-analytics/*` | Frontend requests routed through gateway |
| web-scms → APEX | **Inbound HTTP** | `fetch()` calls | Dashboard + AI recommendation endpoints |
| ms-authentication → APEX | **None** (shared JWT secret) | JWT validation | APEX validates tokens using the same `JWT_SECRET` |

> **Key principle:** APEX does not modify existing operational tables in PostgreSQL (`Items`, `PurchaseOrders`, etc.). It stores only into `analytics_documents`.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Framework** | FastAPI (async Python) |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn (regression, classification, forecasting) |
| **Database** | PostgreSQL 15+ (`scm_db` — operational reads + `analytics_documents` writes) |
| **Cache** | In-Memory (TTL-based caching) |
| **Server** | Uvicorn (ASGI) |
| **Validation** | Pydantic v2 + pydantic-settings |
| **HTTP Client** | httpx (async) |
| **Auth** | PyJWT (HS256 symmetric validation) |

## Prerequisites

- [Python](https://www.python.org/) 3.12+
- [PostgreSQL](https://www.postgresql.org/) 15+ — the `scm_db` database must exist (created by `api-scms`)

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/beanszza/APEX.git
cd APEX
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` with your local values. See [Configuration](#configuration) for details.

### 5. Start databases

Ensure PostgreSQL (with `scm_db`), MongoDB, and Redis are running:

```bash
# Verify PostgreSQL (scm_db should already exist from api-scms)
psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname = 'scm_db';"

# Verify MongoDB
mongosh --eval "db.runCommand({ping:1})"     # → { ok: 1 }

# Verify Redis
redis-cli ping                                # → PONG
```

### 6. Run the service

```bash
uvicorn app.main:app --reload --port 5011
```

You should see:

```
INFO:     Connecting to PostgreSQL (scm_db) — read-only
INFO:     PostgreSQL connected
INFO:     Connecting to MongoDB at mongodb://localhost:27017
INFO:     MongoDB connected
INFO:     Connecting to Redis at redis://localhost:6379/0
INFO:     Redis connected
INFO:     APScheduler started with periodic_analytics_compile job
INFO:     Uvicorn running on http://0.0.0.0:5011
```

### 7. Access the API

- **API Docs (Scalar)**: http://localhost:5011/docs
- **OpenAPI JSON**: http://localhost:5011/openapi.json
- **Health Check**: http://localhost:5011/health

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (`development` / `production`) | `development` |
| `APP_HOST` | Bind address | `0.0.0.0` |
| `APP_PORT` | Server port | `5011` |
| **PostgreSQL (read-only)** | | |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name (same as api-scms) | `scm_db` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `password` |
| **MongoDB** | | |
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DATABASE` | Database name | `apex_db` |
| **Redis** | | |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| **Auth (JWT)** | | |
| `JWT_SECRET` | Shared JWT secret (same as ms-authentication) | — |
| `JWT_ISSUER` | JWT issuer URL | `http://localhost:5007` |
| `JWT_AUDIENCE` | JWT audience | `http://localhost:3000` |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/analytics/dashboard` | Dashboard stats (KPIs, charts, alerts) |
| `GET` | `/api/analytics/ai` | AI recommendations (procurement + production) |
| `POST` | `/api/analytics/compile` | Trigger analytics recompilation |

### Response Format

All endpoints return a consistent response envelope:

```json
{
  "success": true,
  "message": "Dashboard analytics fetched from Redis cache",
  "data": { ... }
}
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     APEX Data Pipeline                       │
│                                                             │
│   PostgreSQL (scm_db)                                       │
│   ┌──────────────────────────┐                              │
│   │ Items + Inventories      │                              │
│   │ PurchaseOrders + Items   │──── READ-ONLY SQL ────┐      │
│   │ ProductionBatches        │                       │      │
│   │ StockTransfers           │                       │      │
│   │ Suppliers                │                       │      │
│   └──────────────────────────┘                       │      │
│                                                      ▼      │
│                                              ┌──────────┐   │
│                                              │  Pandas  │   │
│                                              │ DataFrame│   │
│                                              └────┬─────┘   │
│                                                   │         │
│                              ┌────────────────────┼────┐    │
│                              │                    │    │    │
│                              ▼                    ▼    ▼    │
│                       ┌────────────┐  ┌────────┐ ┌──────┐  │
│                       │ Scikit-    │  │ NumPy  │ │Pandas│  │
│                       │ learn ML   │  │ calcs  │ │ agg  │  │
│                       └─────┬──────┘  └───┬────┘ └──┬───┘  │
│                             │             │         │      │
│                             └─────────┬───┘         │      │
│                                       ▼             │      │
│                              ┌──────────────┐       │      │
│                              │ AI Recommend │       │      │
│                              │ ations       │       │      │
│                              └──────┬───────┘       │      │
│                                     │               │      │
│            ┌────────────────────────┼───────────────┘      │
│            ▼                        ▼                       │
│   ┌──────────────┐        ┌──────────────┐                 │
│   │   MongoDB    │        │    Redis     │                 │
│   │  (persist)   │        │   (cache)    │                 │
│   └──────────────┘        └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
APEX/
├── app/
│   ├── main.py                        → FastAPI app + lifespan (DB connections)
│   ├── api/
│   │   └── routes/
│   │       ├── dashboard.py           → GET /api/analytics/dashboard
│   │       ├── recommendations.py     → GET /api/analytics/ai
│   │       └── compile.py             → POST /api/analytics/compile
│   ├── core/
│   │   ├── config.py                  → Pydantic Settings (env vars)
│   │   ├── auth.py                    → JWT validation (shared secret)
│   │   └── scheduler.py              → APScheduler (periodic compilation)
│   ├── db/
│   │   ├── postgres.py                → SQLAlchemy read-only engine
│   │   ├── mongo.py                   → Motor async MongoDB client
│   │   └── redis.py                   → Async Redis client
│   ├── services/
│   │   └── analytics_compiler.py      → Core analytics compilation logic
│   ├── ml/
│   │   ├── demand_forecaster.py       → Scikit-learn demand prediction
│   │   └── reorder_optimizer.py       → Reorder quantity optimization
│   ├── models/
│   │   ├── dashboard.py               → Dashboard Pydantic models
│   │   └── recommendations.py         → AI recommendation Pydantic models
│   ├── schemas/                       → API request/response schemas
│   └── helpers/                       → Utility functions
├── tests/                             → Pytest test suite
├── .env.example                       → Environment variable documentation
├── .gitignore                         → Git ignore rules
├── requirements.txt                   → Python dependencies
├── Dockerfile                         → Production container
├── LICENSE                            → MIT License
└── README.md                          → This file
```

## Running with the R3B2P Ecosystem

APEX is designed to run alongside the existing R3B2P microservices:

| Service | Repo | Port | Status |
|---------|------|------|--------|
| host-app | `host-app` | `:3000` | Existing |
| web-scms | `web-scms` | `:3004` | Existing |
| api-gateway | `api-gateway` | `:5001` | Existing — add 1 route for APEX |
| api-scms | `api-scms` | `:5006` | Existing — no changes needed |
| ms-authentication | `ms-authentication` | `:5007` | Existing — no changes needed |
| **APEX** | **APEX** | **`:5011`** | **New** |

### Gateway Configuration

Add this route to `api-gateway/appsettings.json` to expose APEX through the gateway:

```json
{
  "Routes": {
    "scms-analytics-route": {
      "ClusterId": "scms-analytics-cluster",
      "Match": { "Path": "/api/scms-analytics/{**catch-all}" },
      "Transforms": [{ "PathRemovePrefix": "/api/scms-analytics" }]
    }
  },
  "Clusters": {
    "scms-analytics-cluster": {
      "Destinations": {
        "scms-analytics-destination": {
          "Address": "http://localhost:5011/"
        }
      }
    }
  }
}
```

### Start All Services

```bash
# Terminal 1 — api-scms
cd api-scms && dotnet run

# Terminal 2 — ms-authentication
cd ms-authentication && dotnet run

# Terminal 3 — api-gateway
cd api-gateway && dotnet run

# Terminal 4 — APEX (this repo)
cd APEX && .venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 5011

# Terminal 5 — web-scms
cd web-scms && npm run dev

# Terminal 6 — host-app
cd host-app && npm run dev
```

## Testing

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1    # Windows
source .venv/bin/activate      # macOS / Linux

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

## License

This project is licensed under the [MIT License](LICENSE).
