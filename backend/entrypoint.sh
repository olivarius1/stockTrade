#!/bin/sh
set -e

echo "Initializing database..."
python init_db.py

echo "Starting backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000