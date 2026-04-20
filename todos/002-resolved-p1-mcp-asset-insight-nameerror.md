---
status: resolved
priority: p1
issue_id: "002"
tags: [code-review, mcp, ai, api, correctness]
dependencies: []
resolved_date: 2026-04-20
---

# Restore MCP asset insight agent lookup

## Status: ✅ RESOLVED

**Solution implemented**: Restored the assigned `agent` lookup in `backend/mcp/views.py`, so valid agent tokens can reach the asset insight path again.

## Problem Statement

`POST /api/mcp/asset-insight/` now crashes for valid agent tokens because the view no longer keeps the `AgentToken` object it later dereferences. This breaks agent-side asset insight generation entirely.

## Findings

- In [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L173), the PR changed `agent = AgentToken.objects.get(...)` to a bare `AgentToken.objects.get(...)`.
- The same method still constructs `AIService(agent.user)` at [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L189), so every successful token validation path now hits `NameError: name 'agent' is not defined`.
- There is no MCP view test covering the asset insight happy path, so this regression shipped without detection.

## Proposed Solutions

### Option 1: Restore the assigned lookup

**Approach:** Change the validation line back to `agent = AgentToken.objects.get(token=agent_token)` and keep the rest of the flow intact.

**Pros:**
- Smallest possible fix
- Restores the endpoint behavior expected by the surrounding code

**Cons:**
- Keeps manual token validation duplicated in multiple MCP views

**Effort:** < 30 minutes

**Risk:** Low

---

### Option 2: Reuse shared token verification

**Approach:** Introduce a shared helper that fetches the `AgentToken` once, updates `last_used_at`, and returns the token object to MCP views.

**Pros:**
- Fixes this regression and reduces copy/paste auth mistakes
- Improves agent activity tracking consistency

**Cons:**
- Slightly larger change
- Needs extra regression coverage across multiple endpoints

**Effort:** 1-2 hours

**Risk:** Medium

## Recommended Action

**To be filled during triage.**

## Technical Details

**Affected files:**
- [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L156)
- [backend/mcp/test_views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/test_views.py)

**Related components:**
- MCP agent auth flow
- `AIService.analyze_asset`

**Database changes (if any):**
- Migration needed: No

## Resources

- **PR:** [#30](https://github.com/schonarth/pivot/pull/30)
- **Merge commit:** `785d8433e6e9f8761270a1e6679eca3d4b1ca55e`

## Acceptance Criteria

- [ ] `POST /api/mcp/asset-insight/` succeeds for a valid agent token
- [ ] Invalid tokens still return `401`
- [ ] A regression test covers the successful MCP asset insight path

## Work Log

### 2026-04-19 - Review discovery

**By:** Codex

**Actions:**
- Reviewed the PR diff for [backend/mcp/views.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/mcp/views.py#L173)
- Compared the token lookup block with the later `AIService(agent.user)` call
- Confirmed the assigned `agent` variable was removed in the merged patch

**Learnings:**
- The endpoint currently fails before any AI call is made
- Existing MCP tests cover token exchange and lookup, but not asset insight success

## Notes

- This is a merge-blocking regression for MCP asset insight consumers.
