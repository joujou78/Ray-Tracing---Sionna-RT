#!/usr/bin/env bash
# Start the RF coverage tool on http://localhost:8000
cd "$(dirname "$0")"
exec uvicorn rfcov.api:app --app-dir backend --host 127.0.0.1 --port "${PORT:-8000}" "$@"
