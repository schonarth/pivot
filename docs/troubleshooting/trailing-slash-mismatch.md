# Trailing Slash Mismatch Issue

## Problem

URL pattern definitions in Django don't match incoming requests when trailing slashes differ:

- URL pattern: `path("markets/status", ...)`  
- Request: `GET /api/markets/status/` (with slash)
- Result: Django doesn't match → 404 or silent error

This is especially problematic because:
1. The endpoint exists but appears broken
2. Error handling may return generic/empty error responses
3. Debugging wastes hours chasing the "real" bug in view logic
4. **It happens frequently because HTTP clients often normalize URLs with trailing slashes**

## Root Cause

Django's URL router requires exact path matching (by default). Most HTTP clients and frameworks (axios, fetch, curl) append trailing slashes to paths automatically. The mismatch causes silent failures.

## Proactive Detection

### Before Deployment

**1. Lint Check (add to pre-commit)**
```bash
# Find all url() and path() definitions without trailing slashes
grep -rn 'path("' backend/ | grep -v '/"\|/$"' | grep -v '__'
```

**2. Code Review Checklist**
- [ ] All URL patterns use trailing slashes: `path("endpoint/", ...)`
- [ ] Exception: only root paths like `path("", ...)` omit slashes
- [ ] All ViewSet registrations use slashes: `register(r"assets/", ...)`

**3. Test All Endpoints**
```bash
# Quick validation of all registered endpoints
pytest tests/test_urls.py  # if exists
# Or manually: curl -H "Auth: ..." http://localhost:8000/api/endpoint/
```

### During Development

**1. URL Pattern Template**
Always start with trailing slash:
```python
# ✅ Correct
path("markets/status/", MarketStatusView.as_view(...))
path("agents/", AgentsListView.as_view(...))

# ❌ Wrong
path("markets/status", MarketStatusView.as_view(...))
path("agents", AgentsListView.as_view(...))
```

**2. Exception: Root Paths Only**
```python
# ✅ Correct (no slash for root)
path("", MCPSchemaView.as_view())

# ❌ Wrong
path("/", MCPSchemaView.as_view())
```

**3. Router Patterns**
```python
# ✅ Correct (routers auto-handle slashes with register)
router.register(r"assets", AssetViewSet)  # Becomes /assets/ and /assets/{id}/

# But manual paths still need explicit slashes:
path("assets/", AssetViewSet.as_view(...))  # ✅
path("assets", AssetViewSet.as_view(...))   # ❌
```

## Fix Process

### Quick Fix
Add trailing slash to the URL pattern:
```python
# Before
path("markets/status", MarketStatusView.as_view({"get": "list"}))

# After
path("markets/status/", MarketStatusView.as_view({"get": "list"}))
```

### Verify Fix
```bash
# Test with trailing slash
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/markets/status/

# Test without slash (should still work if APPEND_SLASH=True in Django)
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/markets/status
```

## Prevention Strategy

### 1. Django Settings
In `backend/config/settings.py`, ensure:
```python
APPEND_SLASH = True  # Auto-redirect /path to /path/
```
This is Django's default but verify it's enabled. This makes the system more forgiving but doesn't replace proper pattern definition.

### 2. Code Template
Create a snippet in your IDE for URL patterns:
```python
path("endpoint/", ViewName.as_view(...), name="..."),
```

### 3. Git Hooks
Add pre-commit check:
```bash
# .git/hooks/pre-commit
grep -rn 'path(".*",' backend/ | grep -v '/"\|__\|^.*#' && {
  echo "❌ Found URL patterns without trailing slashes"
  exit 1
}
```

### 4. URL Registry Document
Maintain a list of all endpoints with trailing slash status:
```
/api/mcp/                        ✓
/api/mcp/otp/generate/          ✓
/api/mcp/token/exchange/        ✓
/api/mcp/agents/                ✓
/api/mcp/portfolios/            ✓ (redirect)
/api/markets/status/            ✓
/api/assets/                     ✓
```

## Recent Incidents

| Date | Endpoint | Issue | Fix |
|------|----------|-------|-----|
| 2026-04-14 | `/api/markets/status` | Missing trailing slash, returned empty error | Added `/` |
| 2026-04-14 | `/api/mcp/portfolios/` | No endpoint | Added 307 redirect to `/api/portfolios/` |

## Testing Command

Quick validation script:
```bash
# Test all endpoints at once
for endpoint in \
  "mcp/" \
  "mcp/otp/generate/" \
  "mcp/token/exchange/" \
  "mcp/agents/" \
  "portfolios/" \
  "assets/" \
  "markets/status/"; do
  echo "Testing /api/$endpoint"
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "Authorization: Bearer TEST" \
    http://localhost:8000/api/$endpoint
done
```

## Key Takeaway

**Always use trailing slashes in URL patterns.** It's the single most common source of silent API failures in this codebase. Make it non-negotiable in code review.
