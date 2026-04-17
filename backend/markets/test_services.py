from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from markets.services import is_market_open


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
