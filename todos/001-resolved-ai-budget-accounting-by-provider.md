---
status: resolved
priority: p2
issue_id: "001"
tags: [code-review, security, quality]
dependencies: []
resolved_date: 2026-04-13
solution_doc: docs/solutions/ai-budget-accounting-non-openai-providers.md
---

# AI budget accounting ignores non-OpenAI providers

## Status: ✅ RESOLVED

**Solution implemented**: Provider-specific cost estimation for Anthropic and Google. See `docs/solutions/ai-budget-accounting-non-openai-providers.md` for complete details.

## Summary of Fix

Added cost estimation methods in `backend/ai/services.py`:
- `_estimate_anthropic_cost()` - Anthropic pricing tables
- `_estimate_google_cost()` - Google Gemini pricing tables  
- `_estimate_provider_cost()` - unified dispatcher

Updated `analyze_asset()` to calculate costs for all providers before logging, ensuring budget enforcement works consistently.

## Acceptance Criteria

- ✅ Anthropic and Google calls record non-zero USD usage
- ✅ Monthly budget totals include all supported providers
- ✅ Budget limit checks stop AI requests regardless of provider
- ✅ Regression test covers non-OpenAI provider cost calculation (line 48-51 in `test_views.py`)

---

## Original Problem Statement

AI usage tracking only assigned a real USD cost for OpenAI calls. Anthropic and Google requests were allowed but logged with zero cost, bypassing budget controls.

**Affected code**: `backend/ai/services.py:270-303`

**Impact**: Non-OpenAI users could keep generating AI calls after believing they exceeded budget.
