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