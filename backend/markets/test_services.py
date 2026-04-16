from types import SimpleNamespace
from unittest.mock import patch

import pytest

from markets.models import NewsItem
from markets.services import NewsService


def make_feed_entry(title, link, published="Wed, 16 Apr 2026 12:00:00 GMT", summary="Summary"):
    return {
        "title": title,
        "link": link,
        "published": published,
        "summary": summary,
    }


@pytest.mark.django_db
class TestNewsService:
    def test_fetch_google_news_rss_returns_entries_for_asset_queries(self, asset):
        feed = SimpleNamespace(entries=[
            make_feed_entry("Apple rallies on services growth", "https://example.com/apple-1"),
            make_feed_entry("Apple supply chain update", "https://example.com/apple-2"),
        ])

        with patch("markets.services.feedparser.parse", return_value=feed) as parse:
            items = NewsService._fetch_google_news_rss(asset)

        assert len(items) == 2
        assert items[0]["source"] == "google_news_rss"
        assert items[0]["published_at"] is not None
        assert parse.call_count >= 1

    def test_fetch_and_store_news_persists_google_news_results(self, asset):
        feed = SimpleNamespace(entries=[
            make_feed_entry("Momentum improves after earnings", "https://example.com/news-1"),
            make_feed_entry("Supply chain remains stable", "https://example.com/news-2"),
        ])

        with patch("markets.services.feedparser.parse", return_value=feed), patch(
            "markets.services.NewsService._fetch_yahoo_finance", return_value=[]
        ), patch(
            "markets.services.NewsService._fetch_marketwatch", return_value=[]
        ), patch(
            "markets.services.NewsService._fetch_rss_fallback", return_value=[]
        ), patch(
            "ai.services.AIService.analyze_news_sentiment",
            return_value={
                "Momentum improves after earnings": 0.4,
                "Supply chain remains stable": 0.1,
            },
        ):
            count = NewsService.fetch_and_store_news(asset)

        stored = NewsItem.objects.filter(asset=asset).order_by("-published_at", "-fetched_at")

        assert count == 2
        assert stored.count() == 2
        assert stored.first().source == "google_news_rss"
        assert stored.first().sentiment_score is not None

    def test_fetch_and_store_news_uses_short_cache_for_empty_results(self, asset):
        with patch("markets.services.cache.set") as cache_set, patch(
            "markets.services.NewsService._fetch_google_news_rss", return_value=[]
        ), patch(
            "markets.services.NewsService._fetch_yahoo_finance", return_value=[]
        ), patch(
            "markets.services.NewsService._fetch_marketwatch", return_value=[]
        ), patch(
            "markets.services.NewsService._fetch_rss_fallback", return_value=[]
        ):
            count = NewsService.fetch_and_store_news(asset)

        assert count == 0
        cache_set.assert_called_once_with(f"news:{asset.id}", True, NewsService.EMPTY_CACHE_TTL)
