---
name: AI Budget Accounting for Non-OpenAI Providers
description: Fix zero-cost accounting bug for Anthropic and Google AI requests
type: logic-errors
issue_id: "001"
tags: [ai-services, budget-accounting, cost-tracking]
severity: high
status: resolved
---

# AI Budget Accounting for Non-OpenAI Providers

## Problem

AI usage tracking only assigned real USD cost for OpenAI calls. Anthropic and Google requests were still allowed, but they were logged with zero cost. This caused:
- Monthly usage totals underreported actual spend
- Budget enforcement bypassed for non-OpenAI providers
- Users could exceed actual spend while believing they were within budget

### Root Cause

`backend/ai/services.py:270-303` computed `cost_usd` only for the OpenAI branch. Anthropic and Google branches left `cost_usd` at `Decimal("0")`, then `log_call()` stored that value in `AICost`. Both `get_monthly_usage_usd()` and `check_budget()` relied on `AICost.cost_usd`, so non-OpenAI usage bypassed budget controls.

## Solution Implemented

Added provider-specific cost estimation methods before logging any AI call.

### Key Changes

**File**: `backend/ai/services.py`

1. **Added cost estimation methods** (lines 181-214):
   - `_estimate_anthropic_cost()` - pricing for Haiku, Sonnet, Opus models
   - `_estimate_google_cost()` - pricing for Gemini 2.0 Flash and 1.5 Pro
   - `_estimate_provider_cost()` - unified dispatcher for all providers

2. **Updated `analyze_asset()` method** (line 361):
   - Now calls `self._estimate_provider_cost()` with actual provider, model, and token counts
   - Calculates cost **before** calling `log_call()`
   - Works identically for all supported providers

### Pricing Tables

```python
# Anthropic (per token)
"claude-haiku-4-5-20251001": ($0.0000008, $0.000004)      # prompt, completion
"claude-sonnet-4-6": ($0.000003, $0.000015)
"claude-opus-4-6": ($0.000015, $0.000075)

# Google Gemini (per token)
"gemini-2.0-flash": ($0.00000035, $0.00000105)
"gemini-1.5-pro": ($0.00000125, $0.000005)

# OpenAI (per token)
"gpt-4o-mini": ($0.00000015, $0.0000006)
"gpt-4o": ($0.0000025, $0.00001)
```

## Verification

**Test**: `backend/ai/test_views.py::test_provider_cost_estimation_is_non_zero_for_supported_non_openai_models`

```python
cost = AIService._estimate_provider_cost("anthropic", "claude-opus-4-6", 1000, 500)
assert cost > 0  # ✓ now passes
```

## Acceptance Criteria Met

- ✅ Anthropic and Google calls record non-zero USD usage
- ✅ Monthly budget totals include all supported providers
- ✅ Budget limit checks stop AI requests regardless of provider
- ✅ Regression test covers non-OpenAI provider cost calculation

## Impact

- **Scope**: Affects all `analyze_asset()` calls via indicators page
- **Backward compatibility**: None — only fixes underreporting
- **Performance**: Negligible — just arithmetic on token counts
- **Security**: No changes to auth or key handling

## Related

- AI settings UI budget display (`src/components/AISettings.vue`)
- Monthly budget enforcement in `AIService.check_budget()`
- Token-to-cost conversion happens at call time before logging
