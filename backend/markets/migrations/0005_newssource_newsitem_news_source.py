import django.db.models.deletion
from django.db import migrations, models

NEWS_SOURCES = (
    ("Google News", "https://news.google.com/rss/search", None),
    ("Yahoo Finance", "https://finance.yahoo.com/quote/{symbol}/news", None),
    ("Yahoo Finance", "https://feeds.finance.yahoo.com/news", "US"),
    ("MarketWatch", "https://www.marketwatch.com/investing/stock/{symbol}", None),
    ("Valor Econômico", "https://www.valor.com.br/search", "BR"),
    ("Bloomberg", "http://feeds.bloomberg.com/markets/news.rss?country=BR", "BR"),
    ("Bloomberg", "http://feeds.bloomberg.com/markets/news.rss?country=UK", "UK"),
    ("Bloomberg", "http://feeds.bloomberg.com/markets/news.rss?country=EU", "EU"),
)

SOURCE_URLS = {
    "google_news_rss": "https://news.google.com/rss/search",
    "yahoo_finance": "https://finance.yahoo.com/quote/{symbol}/news",
    "marketwatch": "https://www.marketwatch.com/investing/stock/{symbol}",
    "valor_economico": "https://www.valor.com.br/search",
}

RSS_URLS = {
    "BR": "http://feeds.bloomberg.com/markets/news.rss?country=BR",
    "US": "https://feeds.finance.yahoo.com/news",
    "UK": "http://feeds.bloomberg.com/markets/news.rss?country=UK",
    "EU": "http://feeds.bloomberg.com/markets/news.rss?country=EU",
}


def seed_sources_and_migrate_news_items(apps, schema_editor):
    NewsItem = apps.get_model("markets", "NewsItem")
    NewsSource = apps.get_model("markets", "NewsSource")

    source_ids = {}
    for institution_name, feed_url, market in NEWS_SOURCES:
        source, _ = NewsSource.objects.get_or_create(
            feed_url=feed_url,
            defaults={
                "institution_name": institution_name,
                "market": market,
                "is_system_managed": True,
            },
        )
        source_ids[feed_url] = source.id

    news_items = list(NewsItem.objects.select_related("asset").all())
    for news_item in news_items:
        if news_item.source == "rss_feed":
            feed_url = RSS_URLS.get(news_item.asset.market)
        else:
            feed_url = SOURCE_URLS.get(news_item.source)
        if not feed_url:
            raise RuntimeError(
                f"Cannot map NewsItem {news_item.pk} source {news_item.source!r} for market {news_item.asset.market!r}"
            )
        news_item.news_source_id = source_ids[feed_url]

    NewsItem.objects.bulk_update(news_items, ["news_source"])


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0004_newsitem"),
    ]

    operations = [
        migrations.CreateModel(
            name="NewsSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("institution_name", models.CharField(max_length=100)),
                ("feed_url", models.URLField(max_length=500, unique=True)),
                ("market", models.CharField(blank=True, max_length=5, null=True)),
                ("is_system_managed", models.BooleanField(default=True, editable=False)),
            ],
            options={"db_table": "news_sources"},
        ),
        migrations.AddField(
            model_name="newsitem",
            name="news_source",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="news_items",
                to="markets.newssource",
            ),
        ),
        migrations.RunPython(seed_sources_and_migrate_news_items, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="newsitem",
            name="news_source",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="news_items",
                to="markets.newssource",
            ),
        ),
    ]
