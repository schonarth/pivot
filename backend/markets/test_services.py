from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from markets.models import Asset, NewsItem
from markets.services import NewsService, is_market_open


@pytest.mark.django_db
class TestMarketOpenService:
    @patch("markets.services.get_calendar")
    @patch("markets.services.timezone.now")
    def test_is_market_open_is_false_after_session_close(self, mock_now, mock_get_calendar):
        mock_now.return_value = timezone.make_aware(datetime(2026, 4, 17, 21, 30))

        calendar = MagicMock()
        calendar.is_session.return_value = True
        calendar.session_open.return_value = timezone.make_aware(datetime(2026, 4, 17, 13, 30))
        calendar.session_close.return_value = timezone.make_aware(datetime(2026, 4, 17, 20, 0))
        mock_get_calendar.return_value = calendar

        assert is_market_open("US") is False

    @patch("markets.services.get_calendar")
    @patch("markets.services.timezone.now")
    def test_is_market_open_is_true_during_session(self, mock_now, mock_get_calendar):
        mock_now.return_value = timezone.make_aware(datetime(2026, 4, 17, 15, 0))

        calendar = MagicMock()
        calendar.is_session.return_value = True
        calendar.session_open.return_value = timezone.make_aware(datetime(2026, 4, 17, 13, 30))
        calendar.session_close.return_value = timezone.make_aware(datetime(2026, 4, 17, 20, 0))
        mock_get_calendar.return_value = calendar

        assert is_market_open("US") is True


@pytest.mark.django_db
class TestNewsService:
    def test_store_news_items_links_rss_fallback_to_market_source(self):
        asset = Asset.objects.create(
            display_symbol="SHEL",
            provider_symbol="SHEL.L",
            name="Shell",
            market="UK",
            exchange="XLON",
            currency="GBP",
        )

        with patch.object(NewsService, "_attach_sentiment_scores"):
            NewsService._store_news_items(
                asset,
                [{
                    "headline": "Shell market update",
                    "url": "https://example.com/shell-update",
                    "source": "rss_feed",
                    "published_at": timezone.now(),
                }],
            )

        stored = NewsItem.objects.get(asset=asset)

        assert stored.source == "rss_feed"
        assert stored.news_source.institution_name == "Bloomberg"
        assert stored.news_source.feed_url == "http://feeds.bloomberg.com/markets/news.rss?country=UK"

    def test_google_news_queries_treat_sqli_shaped_asset_fields_as_plain_text(self):
        asset = Asset.objects.create(
            display_symbol="AAPL'; DROP TABLE news_items;--",
            provider_symbol="AAPL'; SELECT pg_sleep(1);--",
            name='Apple"; DELETE FROM assets;--',
            market="US",
            exchange="XNYS",
            currency="USD",
        )

        queries = NewsService._google_news_queries(asset)

        assert queries[0] == "AAPL'; SELECT pg_sleep(1);--"
        assert queries[1] == "AAPL'; DROP TABLE news_items;--"
        assert queries[2] == '"Apple"; DELETE FROM assets;--"'

    def test_store_news_items_rejects_unknown_source_labels(self):
        asset = Asset.objects.create(
            display_symbol="AAPL",
            provider_symbol="AAPL",
            name="Apple",
            market="US",
            exchange="XNYS",
            currency="USD",
        )

        payload = [
            {
                "headline": "Market update'); DROP TABLE news_items;--",
                "summary": "Analyst note\x00 with control chars and   extra spaces",
                "url": "https://example.com/story?id=1';SELECT+1;--",
                "source": "wire');DELETE FROM assets;--",
                "published_at": timezone.now(),
            }
        ]

        with pytest.raises(ValueError, match="Unknown news source label"):
            NewsService._store_news_items(asset, payload)

        assert not NewsItem.objects.filter(asset=asset).exists()
