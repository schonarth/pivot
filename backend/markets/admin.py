from django.contrib import admin
from .models import Asset, AssetQuote, MarketConfig

admin.site.register(MarketConfig)
admin.site.register(Asset)
admin.site.register(AssetQuote)