---
name: News Ingestion Inputs Not Sanitized
description: Asset symbol and name fields used raw in URL construction and search queries, enabling traversal and excessive-length issues
type: security-issues
issue_id: "003"
tags: [input-sanitization, news-ingestion, url-encoding, security, markets]
severity: high
status: resolved
---

# News Ingestion Inputs Not Sanitized

## Problem

`MarketDataService.fetch_and_store_news()` used `asset.provider_symbol`, `asset.display_symbol`, and `asset.name` directly in:
- URL path construction for Yahoo Finance and MarketWatch scrapers
- Query string construction for Valor Econômico scraper
- Search query strings passed to external news APIs

A crafted symbol value (e.g., `AAPL%2F..%2Fadmin` or a symbol containing newlines/null bytes) could:
- Cause URL path traversal in scraped URLs
- Inject unexpected characters into search queries
- Propagate malformed strings into stored `NewsItem` records and later into AI prompts

### Root Cause

`backend/markets/services.py` — three scraper methods and `fetch_and_store_news()`:

```python
# Before: raw asset fields in URLs
url = f"https://finance.yahoo.com/quote/{asset.provider_symbol}/news"
url = f"https://www.marketwatch.com/investing/stock/{asset.provider_symbol.lower()}"
url = f"https://www.valor.com.br/search?q={asset.display_symbol}"
```

No null-byte stripping, whitespace normalization, length capping, or URL encoding applied to the asset fields.

## Solution Implemented

### 1. Added normalization helpers

```python
@staticmethod
def _normalize_news_text(value, *, max_length: int) -> str:
    if value is None:
        return ""
    normalized = " ".join(str(value).replace("\x00", " ").split())
    return normalized[:max_length]

@classmethod
def _normalize_query_value(cls, value, *, max_length: int = 255) -> str:
    return cls._normalize_news_text(value, max_length=max_length)

@classmethod
def _normalize_news_item(cls, item: dict) -> dict | None:
    url = cls._normalize_news_text(item.get("url"), max_length=500)
    headline = cls._normalize_news_text(item.get("headline"), max_length=500)
    source = cls._normalize_news_text(item.get("source"), max_length=100)
    summary = cls._normalize_news_text(item.get("summary"), max_length=1000)
    if not url or not headline or not source:
        return None
    return {"headline": headline, "url": url, "source": source, "summary": summary or None, ...}
```

### 2. Normalize before URL construction + apply `quote()`

```python
# Yahoo Finance
symbol = quote(cls._normalize_query_value(asset.provider_symbol, max_length=100), safe="")
url = f"https://finance.yahoo.com/quote/{symbol}/news"

# MarketWatch
symbol = cls._normalize_query_value(asset.provider_symbol, max_length=100).lower()
url = f"https://www.marketwatch.com/investing/stock/{quote(symbol, safe='')}"

# Valor Econômico
url = (
    "https://www.valor.com.br/search?q="
    f"{quote_plus(cls._normalize_query_value(asset.display_symbol, max_length=50))}"
)
```

### 3. Normalize each ingested news item before storage

```python
normalized_item = cls._normalize_news_item(item)
if not normalized_item:
    continue
news_item, created = NewsItem.objects.update_or_create(
    asset=asset,
    url=normalized_item["url"],
    ...
)
```

## Verification

Tests added in `backend/markets/test_services.py` covering:
- Null bytes stripped from symbol/name/headline fields
- Symbols exceeding max length truncated before URL construction
- Items missing required fields (`url`, `headline`, `source`) dropped
- Normalized symbols produce valid, properly encoded URLs

## Prevention

- Any external-origin string entering a URL must go through `quote()` / `quote_plus()` **after** normalization.
- Normalize at the boundary: strip null bytes, collapse whitespace, cap length **before** the value is used anywhere (URLs, queries, stored records, prompts).
- Use `_normalize_news_text(value, max_length=N)` as the standard helper for all news-derived strings.
- Validate fetched items with `_normalize_news_item()` and drop `None` results before persisting.

## Related

- Prompt injection via news headlines → [`prompt-injection-via-news-data-20260421.md`](./prompt-injection-via-news-data-20260421.md)
- `backend/markets/services.py` — `_normalize_news_text`, `_normalize_query_value`, `_normalize_news_item`
