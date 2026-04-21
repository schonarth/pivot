---
status: complete
priority: p1
issue_id: "008"
tags: [code-review, ai, security, prompt-injection, news]
dependencies: []
resolved_date: 2026-04-21
---

# Harden asset and scope news prompts against prompt injection

## Status: ✅ COMPLETE

**Solution implemented**: Added explicit untrusted-data rules and fenced JSON-formatted news blocks to the asset and scope insight prompts so external headlines are treated as evidence, not instructions.

## Problem Statement

Asset and scope insight prompts interpolated raw external headlines directly into prompt prose. A hostile feed item could compete with the actual prompt instructions and steer model output.

## Findings

- News headlines originate from scraped and RSS-fed external sources in [backend/markets/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/services.py:374).
- `build_indicator_insight_prompt()` and `build_scope_insight_prompt()` inserted those headlines into free-form prompt text in [backend/ai/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py:1243).
- The prompt did not mark the news text as untrusted or tell the model to ignore instructions inside it.

## Proposed Solutions

### Option 1: Add explicit untrusted-data rules and delimiters

**Approach:** Keep the current prompt flow, but add a clear instruction block, delimit raw news as untrusted data, and serialize entries as JSON.

**Pros:**
- Small targeted fix
- Works across current providers
- Leaves the surrounding analysis flow intact

**Cons:**
- Still depends on prompt discipline rather than provider-native guardrails alone

**Effort:** Small

**Risk:** Low

### Option 2: Split all providers into system/user channels plus structured inputs

**Approach:** Rework each provider call to move task rules into system instructions and pass news as separate structured content.

**Pros:**
- Stronger isolation model
- Better long-term posture for article-body ingestion

**Cons:**
- Broader refactor
- Higher test surface

**Effort:** Medium

**Risk:** Medium

## Recommended Action

Implemented Option 1 now. Keep Option 2 available if article bodies materially expand the prompt-injection surface later.

## Acceptance Criteria

- [x] Asset insight prompts identify news text as untrusted external data
- [x] Scope insight prompts identify news text as untrusted external data
- [x] Raw news content is fenced off from prompt instructions with a stable delimiter

## Work Log

### 2026-04-21 - Implementation

**By:** Codex

**Actions:**
- Added untrusted-news prompt rules and delimiter blocks in [backend/ai/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py:1243)
- Switched context-pack and story lines to JSON serialization so hostile strings are quoted rather than embedded as prompt prose

**Learnings:**
- The main gap was not source validation but prompt framing; explicit trust boundaries close most of the current risk without a larger refactor
