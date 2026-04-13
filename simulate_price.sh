#!/usr/bin/env bash
set -euo pipefail
docker compose exec backend python manage.py simulate_price "$@"
