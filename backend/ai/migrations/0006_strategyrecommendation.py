import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0005_aiauth_enabled"),
        ("markets", "0004_newsitem"),
        ("portfolios", "0005_portfoliowatchmembership"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StrategyRecommendation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("candidate_id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ("action", models.CharField(choices=[("BUY", "Buy"), ("SELL", "Sell")], max_length=4)),
                ("quantity", models.PositiveIntegerField()),
                ("candidate", models.JSONField()),
                ("technical_inputs", models.JSONField()),
                ("context_inputs", models.JSONField()),
                ("sentiment_trajectory_inputs", models.JSONField()),
                ("divergence_inputs", models.JSONField(blank=True, null=True)),
                (
                    "verdict",
                    models.CharField(
                        choices=[("approve", "Approve"), ("reject", "Reject"), ("defer", "Defer")],
                        max_length=10,
                    ),
                ),
                ("rationale", models.CharField(max_length=255)),
                ("recorded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="strategy_recommendations",
                        to="markets.asset",
                    ),
                ),
                (
                    "portfolio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="strategy_recommendations",
                        to="portfolios.portfolio",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="strategy_recommendations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "strategy_recommendations",
                "ordering": ["-recorded_at"],
                "indexes": [
                    models.Index(fields=["user", "-recorded_at"], name="strategy_re_user_id_369586_idx"),
                    models.Index(fields=["portfolio", "-recorded_at"], name="strategy_re_portfol_a7c5f2_idx"),
                    models.Index(fields=["asset", "-recorded_at"], name="strategy_re_asset_i_83688c_idx"),
                ],
            },
        ),
    ]
