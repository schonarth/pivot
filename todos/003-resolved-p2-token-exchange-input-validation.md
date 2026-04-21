---
status: resolved
priority: p2
issue_id: "003"
tags: [code-review, mcp, security, validation, api]
dependencies: []
resolved_date: 2026-04-20
---

# Validate token exchange metadata before DB write

## Status: ✅ RESOLVED

**Solution implemented**: Added a DRF serializer for `/api/mcp/token/exchange/` with strict string validation and field length checks before any database write.

## Problem Statement

The public token exchange endpoint now calls string methods on unvalidated request fields and writes them straight into model fields without serializer validation. Malformed metadata can raise `AttributeError` or database errors instead of returning a controlled `400`.

## Findings

- [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L30) calls `.strip()` on `name`, `llm_model`, and `llm_provider` directly from `request.data`.
- If a client submits non-string JSON like `{ "name": 7 }`, the endpoint raises before reaching the explicit missing-field checks.
- The same request path passes raw `name`, `origin`, `llm_provider`, and `llm_model` into `AgentToken.objects.update_or_create(...)` at [backend/mcp/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/services.py#L37) with no max-length validation against [backend/mcp/models.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/models.py#L33).
- Because `TokenExchangeView` is `AllowAny`, this turns malformed public requests into avoidable `500` paths in the auth flow.

## Proposed Solutions

### Option 1: Add a DRF serializer for token exchange

**Approach:** Validate `user_id`, `otp`, `name`, `origin`, `llm_provider`, and `llm_model` with field types and max lengths before any business logic runs.

**Pros:**
- Standard DRF validation and clear `400` responses
- Centralizes field constraints in one place

**Cons:**
- Adds a serializer for a single endpoint

**Effort:** 1-2 hours

**Risk:** Low

---

### Option 2: Manually normalize and bound inputs in the view

**Approach:** Coerce values with `str(...)`, reject non-string-like inputs explicitly, and enforce length checks before calling `generate_agent_token`.

**Pros:**
- Small patch
- Keeps the current view structure

**Cons:**
- Easier to miss future field additions
- Duplicates model constraints in view code

**Effort:** < 1 hour

**Risk:** Medium

## Recommended Action

**To be filled during triage.**

## Technical Details

**Affected files:**
- [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L23)
- [backend/mcp/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/services.py#L34)
- [backend/mcp/models.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/models.py#L30)

**Related components:**
- OTP exchange flow
- AgentToken persistence

**Database changes (if any):**
- Migration needed: No

## Resources

- **PR:** [#30](https://github.com/schonarth/pivot/pull/30)
- **Merge commit:** `785d8433e6e9f8761270a1e6679eca3d4b1ca55e`

## Acceptance Criteria

- [ ] Non-string or oversized metadata on `/api/mcp/token/exchange/` returns `400`, not `500`
- [ ] Valid exchanges still create tokens with `name`, `origin`, `llm_provider`, and `llm_model`
- [ ] Regression tests cover malformed metadata types and length boundaries

## Work Log

### 2026-04-19 - Review discovery

**By:** Codex

**Actions:**
- Inspected the merged token exchange changes in [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L27)
- Traced the request fields into [backend/mcp/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/services.py#L37)
- Compared the raw writes against `AgentToken` field limits in [backend/mcp/models.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/models.py#L33)

**Learnings:**
- The new metadata requirements shipped without serializer-backed validation
- This is an auth-surface robustness regression, not just a test gap

## Notes

- The fix should preserve the new metadata requirement while making failures deterministic.
