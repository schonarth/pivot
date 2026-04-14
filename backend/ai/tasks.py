from celery import shared_task
from django.core.cache import cache
from decimal import Decimal
import logging

logger = logging.getLogger("paper_trader.ai")


@shared_task
def analyze_news_sentiment():
    """Analyze sentiment for recent news items without sentiment scores."""
    from markets.models import NewsItem
    from ai.services import AIService

    recent_news = NewsItem.objects.filter(sentiment_score__isnull=True).order_by("-fetched_at")[:20]

    if not recent_news:
        return

    headlines = [n.headline for n in recent_news]
    sentiments = AIService.analyze_news_sentiment(headlines)

    if not sentiments:
        logger.warning("No sentiment scores returned from AI")
        return

    for news_item in recent_news:
        if news_item.headline in sentiments:
            score = sentiments[news_item.headline]
            score_decimal = Decimal(str(score)) if not isinstance(score, Decimal) else score
            score_decimal = max(Decimal("-1.0"), min(Decimal("1.0"), score_decimal))
            news_item.sentiment_score = score_decimal
            news_item.save(update_fields=["sentiment_score"])

    logger.info(f"Updated sentiment scores for {len(sentiments)} news items")
