---
name: Known Bug Patterns
description: Real bugs already encountered in the codebase
type: reference
---

# Known Bug Patterns

These are real bugs that have been encountered and should be avoided:

## 1. Route param `undefined` in API calls

**Pattern**: Vue Router params are undefined when component mounts before route resolution completes.

**Fix**: Always use `props: true` **and** `useRoute()` fallback
```typescript
const route = useRoute()
const id = props.id || route.params.id
```

## 2. `QuerySet.aggregate()` with raw Python values

**Pattern**: Using raw Python values in aggregate calculations loses type safety.

**Fix**: Use `Sum()`, `Count()`, `Avg()`, etc.
```python
# Bad:
total = qs.aggregate(total=Sum('amount'))['total'] or 0

# Good:
from django.db.models import Sum, Value
total = qs.aggregate(total=Sum('amount', default=Value(0)))['total']
```

## 3. f-string vs literal string in `publish_event()` calls

**Pattern**: Mismatched string formatting in real-time event publishing.

**Fix**: Verify all arguments are properly formatted before passing to `publish_event()`

## 4. Trailing slash mismatches in DRF endpoints

**Pattern**: POST requests lose auth headers when redirected due to trailing slash mismatch.

**Fix**: Always match DRF router's trailing slash configuration
