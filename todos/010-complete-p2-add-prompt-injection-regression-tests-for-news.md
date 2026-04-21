---
status: complete
priority: p2
issue_id: "010"
tags: [code-review, ai, tests, security, prompt-injection]
dependencies: []
resolved_date: 2026-04-21
---

# Add prompt-injection regression tests for news-driven AI prompts

## Status: ✅ COMPLETE

**Solution implemented**: Added regression coverage that asserts untrusted-news framing is present in asset prompts and that sentiment prompts use indexed untrusted headline records.

## Problem Statement

The prompt tests covered prompt composition, but not hostile headline handling. That left the injection hardening easy to regress.

## Findings

- Existing prompt assertions in [backend/ai/test_context.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/test_context.py:677) checked for section names, not safety framing.
- No test used an adversarial headline payload.
- No test covered the sentiment prompt contract.

## Proposed Solutions

### Option 1: Add focused regression tests around prompt contents

**Approach:** Add tests for hostile headlines, untrusted-data instructions, delimiters, and indexed sentiment records.

**Pros:**
- Cheap and durable
- Protects the exact risk that triggered the review

**Cons:**
- Does not prove provider behavior end to end

**Effort:** Small

**Risk:** Low

## Recommended Action

Implemented Option 1.

## Acceptance Criteria

- [x] Tests cover hostile headline handling in asset insight prompts
- [x] Tests cover untrusted-data framing in sentiment prompts
- [x] Existing prompt-shape tests still pass with the hardened format

## Work Log

### 2026-04-21 - Implementation

**By:** Codex

**Actions:**
- Extended prompt assertions in [backend/ai/test_context.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/test_context.py:677)
- Added hostile-headline and sentiment-prompt regression tests in the same module

**Learnings:**
- Prompt hardening needs content-level assertions, not just section-presence checks
