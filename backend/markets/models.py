import uuid

from django.db import models
from django.conf import settings


class MarketConfig(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3)
    exchange = models.CharField(max_length=10)
    fee_rate = models.DecimalField(max_digits=8, decimal_places=6, default=0)
    iana_timezone = models.CharField(max_length=50)

    class Meta:
        db_table = "market_configs"

    def __str__(self):
        return f"{self.code} ({self.name})"


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    figi = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    display_symbol = models.CharField(max_length=50)
    provider_symbol = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    market = models.CharField(max_length=5)
    exchange = models.CharField(max_length=20)
    currency = models.CharField(max_length=3)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    is_seeded = models.BooleanField(default=False)
    last_symbol_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assets"
        unique_together = [("market", "display_symbol")]
        indexes = [
            models.Index(fields=["market", "display_symbol"]),
        ]

    def __str__(self):
        return f"{self.display_symbol} ({self.market})"


class AssetQuote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="quotes")
    price = models.DecimalField(max_digits=20, decimal_places=4)
    currency = models.CharField(max_length=3)
    source = models.CharField(max_length=50, default="yahoo_finance")
    is_override = models.BooleanField(default=False)
    as_of = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)
    is_delayed = models.BooleanField(default=True)
    provider_payload = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "asset_quotes"
        indexes = [
            models.Index(fields=["asset", "-fetched_at"]),
        ]
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"{self.asset.display_symbol} @ {self.price} ({self.as_of})"


class OHLCV(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="ohlcv_data")
    date = models.DateField(db_index=True)
    open = models.DecimalField(max_digits=20, decimal_places=4)
    high = models.DecimalField(max_digits=20, decimal_places=4)
    low = models.DecimalField(max_digits=20, decimal_places=4)
    close = models.DecimalField(max_digits=20, decimal_places=4)
    volume = models.BigIntegerField()
    source = models.CharField(max_length=50, default="yahoo_finance")
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ohlcv"
        unique_together = [("asset", "date")]
        indexes = [
            models.Index(fields=["asset", "-date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.asset.display_symbol} {self.date} {self.close}"


class TechnicalIndicators(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="technical_indicators")
    date = models.DateField(db_index=True)
    rsi_14 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    macd = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    macd_signal = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    macd_histogram = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    ma_20 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    ma_50 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    ma_200 = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    bb_upper = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    bb_middle = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    bb_lower = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    volume_20d_avg = models.BigIntegerField(null=True, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "technical_indicators"
        unique_together = [("asset", "date")]
        indexes = [
            models.Index(fields=["asset", "-date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.asset.display_symbol} {self.date} indicators"


class NewsItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="news_items")
    headline = models.CharField(max_length=500)
    summary = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=500)
    source = models.CharField(max_length=100)
    sentiment_score = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        help_text="Sentiment score from -1.0 (negative) to +1.0 (positive)"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "news_items"
        indexes = [
            models.Index(fields=["asset", "-published_at"]),
            models.Index(fields=["asset", "-fetched_at"]),
        ]
        ordering = ["-published_at"]

    def __str__(self):
        return f"{self.asset.display_symbol} - {self.headline[:50]}"