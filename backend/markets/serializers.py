from rest_framework import serializers
from .models import Asset, AssetQuote, MarketConfig


class MarketConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketConfig
        fields = ("code", "name", "currency", "exchange", "fee_rate", "iana_timezone")


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = (
            "id",
            "figi",
            "display_symbol",
            "provider_symbol",
            "name",
            "market",
            "exchange",
            "currency",
            "sector",
            "industry",
            "is_seeded",
            "created_at",
        )


class AssetQuoteSerializer(serializers.ModelSerializer):
    asset_symbol = serializers.CharField(source="asset.display_symbol", read_only=True)

    class Meta:
        model = AssetQuote
        fields = (
            "id",
            "asset",
            "asset_symbol",
            "price",
            "currency",
            "source",
            "as_of",
            "fetched_at",
            "is_delayed",
        )