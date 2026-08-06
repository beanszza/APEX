#!/usr/bin/env bash
set -e

echo "=================================================="
echo " Starting APEX Analytics Microservice (:5011)"
echo "=================================================="

# 1. Activate virtual environment if present
if [ -d ".venv" ]; then
  echo "[APEX] Activating virtual environment..."
  source .venv/bin/activate
fi

# 2. Check databases
echo "[APEX] Verifying database connectivity..."
python scripts/ensure-dbs.py

# 3. Launch Uvicorn server
echo "[APEX] Starting Uvicorn server on http://localhost:5011..."
uvicorn app.main:app --reload --port 5011
