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

    def test_store_news_items_persists_hostile_strings_as_data(self):
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

        with patch.object(NewsService, "_attach_sentiment_scores"):
            created = NewsService._store_news_items(asset, payload)

        stored = NewsItem.objects.get(asset=asset)

        assert created == 1
        assert stored.headline == "Market update'); DROP TABLE news_items;--"
        assert stored.summary == "Analyst note with control chars and extra spaces"
        assert stored.url == "https://example.com/story?id=1';SELECT+1;--"
        assert stored.source == "wire');DELETE FROM assets;--"
