---
status: complete
priority: p1
issue_id: "009"
tags: [code-review, ai, security, prompt-injection, ingestion]
dependencies: []
resolved_date: 2026-04-21
---

# Harden news sentiment ingestion prompt against hostile headlines

## Status: ✅ COMPLETE

**Solution implemented**: Reworked the sentiment prompt to treat headlines as untrusted data and return scores by stable numeric id instead of mirroring untrusted headline text in the output schema.

## Problem Statement

The sentiment-analysis prompt fed raw headlines straight into the instruction body and asked the model to emit a JSON object keyed by those same headlines. A malicious headline could influence both instruction following and output structure.

## Findings

- Newly ingested news is automatically sent through `AIService.analyze_news_sentiment()` in [backend/markets/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/markets/services.py:528).
- `build_sentiment_prompt()` previously embedded headlines as free-form bullet text in [backend/ai/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py:1371).
- The parse step trusted model output keyed by untrusted headline strings.

## Proposed Solutions

### Option 1: Use indexed records and untrusted-data instructions

**Approach:** Serialize headlines as `[{id, headline}]`, instruct the model to ignore requests inside headlines, and parse `{items:[{id, sentiment_score}]}`.

**Pros:**
- Eliminates untrusted-text-controlled output keys
- Small contained change
- Easier to validate in tests

**Cons:**
- Changes the internal prompt contract

**Effort:** Small

**Risk:** Low

### Option 2: Replace LLM sentiment with heuristic scoring

**Approach:** Use deterministic keyword scoring instead of an LLM for ingest-time sentiment.

**Pros:**
- Removes this injection surface entirely
- More predictable cost profile

**Cons:**
- Lower quality sentiment coverage
- Bigger product behavior change

**Effort:** Medium

**Risk:** Medium

## Recommended Action

Implemented Option 1. Keep the LLM path, but stop letting hostile headline text define the output schema.

## Acceptance Criteria

- [x] Sentiment prompt labels headlines as untrusted data
- [x] Sentiment prompt uses stable ids instead of headline text as output keys
- [x] Parsing maps model output back to the original headlines safely

## Work Log

### 2026-04-21 - Implementation

**By:** Codex

**Actions:**
- Reworked `build_sentiment_prompt()` and the response parser in [backend/ai/services.py](/Volumes/HomeX/gus/Projects/Lab/paper-trader/backend/ai/services.py:1371)
- Preserved the external `dict[headline, Decimal]` return shape while changing the internal prompt contract

**Learnings:**
- The safest small fix was to remove hostile text from the response schema entirely
