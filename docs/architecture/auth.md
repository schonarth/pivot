---
name: Authentication & Authorization
description: JWT auth, token handling, and access control
type: reference
---

# Authentication & Authorization

## JWT Tokens

- **Access tokens**: 15 min expiry, stored in `localStorage`
- **Refresh tokens**: 7 days expiry, rotated + blacklisted on refresh
- Frontend refreshes automatically on 401 via axios interceptor in `src/api/client.ts`

## Access Control

- All DRF views require `IsAuthenticated`
- All querysets filter by `request.user`
- No public endpoints

## Error Format

All API errors come back as `{"error": {...}}` via the custom handler in `config/exceptions.py`.
