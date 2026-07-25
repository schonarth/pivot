# Backend Conventions

- ASGI entry: `config.asgi:application` (Channels + Daphne).
- WSGI fallback: `config.wsgi:application`.
- Celery broker: `redis://redis:6379/0`; Beat uses the database scheduler.
- All environment variables use `python-decouple`, with defaults in `backend/.env.example`.
- DRF errors use `{"error": {...}}`; see `config/exceptions.py`.

## URL Convention

DRF `DefaultRouter` routes use trailing slashes. Frontend API calls must use them too, for example `/api/portfolios/` and `/api/assets/:id/price/`. A mismatched slash can cause a redirect that loses auth headers or a 404.
