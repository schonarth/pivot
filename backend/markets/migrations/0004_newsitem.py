import django.db.models.deletion
import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0003_ohlcv_technicalindicators"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS news_items (
                        id uuid PRIMARY KEY,
                        headline varchar(500) NOT NULL,
                        summary text NULL,
                        url varchar(500) NOT NULL,
                        source varchar(100) NOT NULL,
                        sentiment_score numeric(3, 2) NULL,
                        published_at timestamp with time zone NULL,
                        fetched_at timestamp with time zone NOT NULL,
                        asset_id uuid NOT NULL REFERENCES assets (id) DEFERRABLE INITIALLY DEFERRED
                    )
                    """,
                    reverse_sql="DROP TABLE IF EXISTS news_items CASCADE",
                ),
                migrations.RunSQL(
                    sql="CREATE INDEX IF NOT EXISTS news_items_asset_i_33677a_idx ON news_items (asset_id, published_at DESC)",
                    reverse_sql="DROP INDEX IF EXISTS news_items_asset_i_33677a_idx",
                ),
                migrations.RunSQL(
                    sql="CREATE INDEX IF NOT EXISTS news_items_asset_i_73014b_idx ON news_items (asset_id, fetched_at DESC)",
                    reverse_sql="DROP INDEX IF EXISTS news_items_asset_i_73014b_idx",
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="NewsItem",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("headline", models.CharField(max_length=500)),
                        ("summary", models.TextField(blank=True, null=True)),
                        ("url", models.URLField(max_length=500)),
                        ("source", models.CharField(max_length=100)),
                        (
                            "sentiment_score",
                            models.DecimalField(
                                blank=True,
                                decimal_places=2,
                                help_text="Sentiment score from -1.0 (negative) to +1.0 (positive)",
                                max_digits=3,
                                null=True,
                            ),
                        ),
                        ("published_at", models.DateTimeField(blank=True, null=True)),
                        ("fetched_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "asset",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="news_items",
                                to="markets.asset",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "news_items",
                        "ordering": ["-published_at"],
                        "indexes": [
                            models.Index(fields=["asset", "-published_at"], name="news_items_asset_i_33677a_idx"),
                            models.Index(fields=["asset", "-fetched_at"], name="news_items_asset_i_73014b_idx"),
                        ],
                    },
                ),
            ],
        ),
    ]
