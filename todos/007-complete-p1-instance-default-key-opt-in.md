---
status: complete
priority: p1
issue_id: "007"
tags: [code-review, frontend, security, ai-settings, ux]
dependencies: []
---

# AI settings silently opts new keys into instance-default mode

## Status: ✅ CLOSED AS DESIGNED

**Decision**: Will not fix. Defaulting instance-default to on is intentional for this product context.

**Rationale**: Pivot is mostly a personal app used in reasonably restricted environments, often by one or a few users. Asset-level news ingestion is an instance process, not user-bound. Defaulting this off would hide a core feature from users who would not realize they must enable it manually. The API-key protection concern is valid, but in this environment the shared instance-default key is acceptable and the UX cost of turning it off by default is higher.

## Problem Statement

Saving a new API key currently defaults `useInstanceDefault` to `true` whenever the instance does not already have a default key. That means a normal personal key save silently promotes the key into the shared instance-default slot unless the user notices and unchecks the box first.

## Findings

- `frontend/src/components/AISettings.vue:294` sets `useInstanceDefault.value = !data.instance_default_enabled || data.instance_default_owned_by_current_user`.
- When there is no existing instance default, the checkbox is preselected before the user takes any sharing action.
- `frontend/src/components/AISettings.vue:389` forwards that value as `use_as_instance_default` during `setApiKey`.
- Backend `backend/ai/views.py:80` treats `use_as_instance_default=true` as a real instance-default write, so this is not just presentation state.

## Proposed Solutions

### Option 1: Default to explicit opt-in

**Approach:** Initialize `useInstanceDefault` to `data.instance_default_owned_by_current_user` and leave it `false` when no instance default exists.

**Pros:**
- Restores least-surprise behavior.
- Avoids accidental key sharing and cost ownership changes.

**Cons:**
- Users who do want instance-default mode need one extra click.

**Effort:** Small

**Risk:** Low

---

### Option 2: Gate instance-default mode behind a confirmation step

**Approach:** Keep the checkbox but require a confirmation modal before the first instance-default save.

**Pros:**
- Preserves current convenience for intentional instance owners.
- Makes the impact explicit.

**Cons:**
- More UI complexity.
- Still leaves a risky default in place.

**Effort:** Medium

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- `frontend/src/components/AISettings.vue:294`
- `frontend/src/components/AISettings.vue:389`
- `backend/ai/views.py:80`

## Resources

- **PR:** #30
- **Review focus:** frontend AI settings flow

## Acceptance Criteria

- [ ] Saving a personal API key does not write an instance-default key unless the user explicitly opts in
- [ ] Existing instance owners still see their current instance-default state reflected correctly
- [ ] A regression test covers the no-instance-default initial load case

## Work Log

### 2026-04-19 - Review capture

**By:** Codex

**Actions:**
- Reviewed the new AI settings state initialization and save path
- Traced the checkbox state from `loadSettings()` into `setApiKey()`
- Verified the backend applies `use_as_instance_default=true` as a real shared-key write

**Learnings:**
- The regression is frontend-driven and changes security/cost semantics without user intent

### 2026-04-20 - Product decision

**By:** Codex

**Actions:**
- Recorded the "will not fix" decision for the instance-default key default
- Renamed the todo to complete status so the ledger reflects the closed-by-design outcome

**Learnings:**
- Not every security-adjacent concern is worth trading away core usability for in this app's deployment context
