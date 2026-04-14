from rest_framework import serializers
from .models import Asset, AssetQuote, MarketConfig, OHLCV, TechnicalIndicators


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


class OHLCVSerializer(serializers.ModelSerializer):
    class Meta:
        model = OHLCV
        fields = (
            "id",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        )


class TechnicalIndicatorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalIndicators
        fields = (
            "id",
            "date",
            "rsi_14",
            "macd",
            "macd_signal",
            "macd_histogram",
            "ma_20",
            "ma_50",
            "ma_200",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "volume_20d_avg",
        )