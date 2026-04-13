@echo off
docker compose exec backend python manage.py simulate_price %*
