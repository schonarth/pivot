---
status: complete
priority: p2
issue_id: "012"
tags: [ai-settings, django-rest-framework, query-observability, n-plus-one, performance]
dependencies: []
---

# Cache AI Settings Instance Default Key Lookup

## Problem Statement

`GET /api/ai/get_settings/` repeats the same `AIInstanceKey` lookup while serializing one settings response. Query observability surfaced this endpoint as a follow-up candidate after the discovery query hotspot was fixed.

This matters because the endpoint is called by frontend AI-access checks and should not run identical database reads for serializer method fields.

## Findings

- `backend/ai/views.py::AISettingsViewSet.get_settings()` loads or creates the current user's `AIAuth`, then serializes it with `AIAuthSettingsSerializer`.
- `backend/ai/serializers.py::AIAuthSettingsSerializer` defines several `SerializerMethodField`s for instance-default state.
- Each method calls `_get_instance_default_key()`.
- `_get_instance_default_key()` currently runs `AIInstanceKey.objects.filter(pk=1).first()` every time.
- The repeated lookup affects:
  - `instance_default_enabled`
  - `instance_default_allow_other_users`
  - `instance_default_owned_by_current_user`
  - `instance_default_owner_username`
  - `can_use_instance_default`

## Proposed Solutions

### Option 1: Cache Lookup on Serializer Instance

**Approach:** Store the first `_get_instance_default_key()` result on the serializer instance and reuse it for all method fields.

**Pros:**
- Smallest local change
- Preserves API response shape
- No view changes needed
- Easy regression test with query capture

**Cons:**
- Keeps the lookup hidden inside serializer methods

**Effort:** 30-60 minutes

**Risk:** Low

---

### Option 2: Pass Preloaded Instance Key Through Serializer Context

**Approach:** Load the instance-default key once in the view and pass it through serializer context.

**Pros:**
- Makes data dependencies explicit at the view boundary
- Avoids serializer-level database access for this field group

**Cons:**
- Slightly broader change
- Requires touching view and serializer together

**Effort:** 1-2 hours

**Risk:** Low

## Recommended Action

Cache the instance-default key lookup on each `AIAuthSettingsSerializer` instance and cover the endpoint with a query-count regression test.

## Technical Details

Affected files:
- `backend/ai/serializers.py` - `AIAuthSettingsSerializer._get_instance_default_key()`
- `backend/ai/test_views.py` - regression coverage for `GET /api/ai/get_settings/`

Database changes:
- None expected.

## Resources

- Related observability ADR: `docs/adrs/ADR-008-global-in-memory-query-observability.md`
- Related solved pattern: `docs/solutions/discovery-query-inputs-bulk-loaded-20260424.md`

## Acceptance Criteria

- [x] `GET /api/ai/get_settings/` response payload remains unchanged
- [x] Instance-default key is fetched no more than once per settings serialization
- [x] Regression test proves repeated serializer method fields do not repeat the same `AIInstanceKey` query
- [x] Targeted AI settings tests pass
- [x] Query observability concern addressed by query-count regression

## Work Log

### 2026-05-07 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed query observability follow-up candidates after PR #40.
- Inspected `AISettingsViewSet.get_settings()` and `AIAuthSettingsSerializer`.
- Identified repeated `AIInstanceKey.objects.filter(pk=1).first()` calls across serializer method fields.

**Learnings:**
- This is the smaller, safer follow-up before portfolio summary quote bulk-loading.

### 2026-05-07 - Implementation

**By:** Codex

**Actions:**
- Cached `AIAuthSettingsSerializer._get_instance_default_key()` on the serializer instance.
- Added `select_related("owner")` to preserve owner username access without an extra owner lookup.
- Added `test_get_settings_fetches_instance_default_once`.
- Ran `docker compose exec backend pytest ai/test_views.py -q`.
- Ran `docker compose exec backend ruff check ai/serializers.py ai/test_views.py`.

**Learnings:**
- Serializer-instance caching keeps on-the-fly key changes safe across requests because each request creates a new serializer.
- The endpoint remains read-only; no same-serialization mutation path is expected.

## Notes

- Completed before reviewing the portfolio summary quote bulk-loading candidate.
