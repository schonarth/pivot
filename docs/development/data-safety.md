# Data Safety

All destructive database operations require explicit user authorization.

Before executing an operation that deletes, resets, or materially modifies persistent data:

1. State exactly what data will change or be deleted.
2. Describe the impact, such as loss of portfolios, trades, and alerts.
3. Offer backup options when preservation is possible.
4. Wait for explicit approval.

Examples include:

- `docker compose down -v`
- `python manage.py flush`
- database migrations that alter structure
- any operation that can delete, modify, or reset persistent data

Never assume a fresh database is acceptable.
