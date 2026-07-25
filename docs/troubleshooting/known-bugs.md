---
name: Known Bug Patterns
description: Real bugs already encountered in the codebase
type: reference
---

# Known Bug Patterns

These are real bugs that have been encountered and should be avoided:

## 1. Route param `undefined` in API calls

**Pattern**: `/api/portfolios/undefined/summary/` occurs when a route param is not passed as a component prop or the component mounts before route resolution completes.

**Fix**: Always use `props: true` **and** `useRoute()` fallback
```typescript
const route = useRoute()
const id = props.id || route.params.id
```

## 2. `QuerySet.aggregate()` with raw Python values

**Pattern**: `QuerySet.aggregate()` accepts expressions, not raw Python values. `.aggregate(total=Decimal("0"))` raises `TypeError`.

**Fix**: Never pass raw Python values; use `Sum()`, `Count()`, `Avg()`, `Value()`, and other Django expressions.
```python
# Bad:
total = qs.aggregate(total=Sum('amount'))['total'] or 0

# Good:
from django.db.models import Sum, Value
total = qs.aggregate(total=Sum('amount', default=Value(0)))['total']
```

## 3. f-string vs literal string in `publish_event()` calls

**Pattern**: `publish_event("portfolio:{portfolio_id}", ...)` is a literal string, not an f-string, so events publish to the wrong channel.

**Fix**: Verify f-string syntax in `realtime/services.py` and `portfolios/services.py` before passing a channel to `publish_event()`.

## 4. Trailing slash mismatches in DRF endpoints

**Pattern**: POST requests lose auth headers when redirected due to trailing slash mismatch.

**Fix**: Always match DRF router's trailing slash configuration
