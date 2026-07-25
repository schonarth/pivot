---
status: complete
priority: p1
issue_id: "013"
tags: [code-review, security, authorization, data-integrity]
dependencies: []
---

# Enforce evidence scope for browser mutations

## Problem Statement

The authenticated browser evidence API resolves news items and sources globally. A user can therefore read evidence for an arbitrary news UUID and create correction, review, or source-stance records for artifacts outside their authorized evidence scope.

## Findings

- `backend/ai/views.py:255-256` fetches any `NewsItem` by ID.
- `backend/ai/views.py:284-320` delegates all mutations to helpers that only resolve global IDs (`backend/ai/views.py:323-329`).
- SPEC-009 requires UI and MCP operations to stay within the authenticated operator's authorized evidence scope. The MCP implementation already enforces this for news items through recommendation context.
- A user can supply another user's (or an unreferenced) `news_item_id` to `POST /api/ai/evidence/corrections/` or `POST /api/ai/evidence/artifact-reviews/`; the API returns 201 and persists an operator-local record for that unrelated artifact.

## Proposed Solutions

### Option 1: Share one scoped-artifact resolver

**Approach:** Move the MCP recommendation-context lookup into a shared evidence service/query helper. Use it from browser and MCP read/mutation endpoints; return 404 for artifacts and sources absent from the caller's stored evidence.

**Pros:**
- One authorization rule across UI and MCP.
- Directly matches the SPEC's scoped-evidence requirement.

**Cons:**
- Requires a small cross-app refactor.

**Effort:** Small

**Risk:** Low

---

### Option 2: Add local filtered queries

**Approach:** Have `EvidenceReviewViewSet` filter candidate IDs by the caller's `StrategyRecommendation.context_inputs`, and verify a source has at least one scoped news item.

**Pros:**
- Minimal immediate change.

**Cons:**
- Duplicates MCP authorization logic and can drift.

**Effort:** Small

**Risk:** Medium

## Recommended Action

Share the scoped evidence resolver between browser and MCP endpoints, then reject artifacts and sources outside the operator's stored recommendation context.

## Technical Details

**Affected files:**
- `backend/ai/views.py:255-329`
- `backend/mcp/views.py:536-652`
- `backend/ai/test_views.py`
- `backend/mcp/test_views.py`

**Database changes:** None expected.

## Resources

- **PR:** https://github.com/schonarth/pivot/pull/44
- **Specification:** `docs/specs/SPEC-009-fact-corrections-and-conflict-detection.md:71,154`

## Acceptance Criteria

- [x] Browser reads and mutations return 404 for an unreferenced or other operator's news item.
- [x] Browser source mutations return 404 unless the source belongs to the caller's scoped evidence.
- [x] UI and MCP use the same authorization rule.
- [x] Cross-user and unreferenced-ID regression tests pass.

## Work Log

### 2026-07-25 - Review discovery

**By:** Codex

**Actions:**
- Compared browser and MCP evidence endpoints.
- Verified browser helper methods use global primary-key lookups while MCP checks recommendation context.

**Learnings:**
- Evidence treatments are operator-local, but their target artifacts still require authorization scoping.

### 2026-07-25 - Completed

**By:** Codex

**Actions:**
- Added an API regression test for foreign evidence and source-stance mutations.
- Added shared scoped news-item and source resolvers to `EvidenceReviewService`.
- Routed browser and MCP evidence endpoints through those resolvers.
- Verified `ai/test_views.py` and `mcp/test_views.py` (18 passed).

**Learnings:**
- Browser and MCP authorization now share one rule, preventing their scopes from drifting.
