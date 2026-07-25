import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0009_artifactreview_factcorrection_sourcestance"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecommendationInvalidation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "artifact_review",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recommendation_invalidations",
                        to="ai.artifactreview",
                    ),
                ),
                (
                    "fact_correction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recommendation_invalidations",
                        to="ai.factcorrection",
                    ),
                ),
                (
                    "recommendation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invalidations",
                        to="ai.strategyrecommendation",
                    ),
                ),
            ],
            options={"db_table": "recommendation_invalidations", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="recommendationinvalidation",
            index=models.Index(
                fields=["recommendation", "-created_at"], name="rec_inv_rec_created_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="recommendationinvalidation",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(("fact_correction__isnull", False), ("artifact_review__isnull", True))
                    | models.Q(("fact_correction__isnull", True), ("artifact_review__isnull", False))
                ),
                name="recommendationinvalidation_single_trigger",
            ),
        ),
        migrations.AddConstraint(
            model_name="recommendationinvalidation",
            constraint=models.UniqueConstraint(
                fields=("recommendation", "fact_correction"), name="unique_recommendation_fact_invalidation"
            ),
        ),
        migrations.AddConstraint(
            model_name="recommendationinvalidation",
            constraint=models.UniqueConstraint(
                fields=("recommendation", "artifact_review"), name="unique_recommendation_review_invalidation"
            ),
        ),
    ]
