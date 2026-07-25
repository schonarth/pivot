import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ai", "0008_strategyscenarioframe"),
        ("markets", "0005_newssource_newsitem_news_source"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArtifactReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_artifact_type", models.CharField(default="news_item", max_length=50)),
                ("source_artifact_id", models.UUIDField()),
                (
                    "artifact_review_state",
                    models.CharField(
                        choices=[("accepted", "Accepted"), ("disputed", "Disputed"), ("stale", "Stale")], max_length=10
                    ),
                ),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("superseded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_artifact_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "operator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="artifact_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="artifact_reviews",
                        to="markets.newssource",
                    ),
                ),
                (
                    "superseded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="superseded_artifact_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "artifact_reviews", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="FactCorrection",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_artifact_type", models.CharField(default="news_item", max_length=50)),
                ("source_artifact_id", models.UUIDField()),
                ("fact_key", models.CharField(max_length=100)),
                ("original_value", models.TextField(editable=False)),
                ("corrected_value", models.TextField()),
                (
                    "correction_state",
                    models.CharField(
                        choices=[("corrected", "Corrected"), ("disputed", "Disputed"), ("stale", "Stale")],
                        max_length=10,
                    ),
                ),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("superseded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_fact_corrections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "operator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fact_corrections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="fact_corrections",
                        to="markets.newssource",
                    ),
                ),
                (
                    "superseded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="superseded_fact_corrections",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "fact_corrections", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="SourceStance",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "stance",
                    models.CharField(choices=[("trusted", "Trusted"), ("untrusted", "Untrusted")], max_length=10),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("superseded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_source_stances",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "operator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_stances",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="source_stances",
                        to="markets.newssource",
                    ),
                ),
                (
                    "superseded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="superseded_source_stances",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": "source_stances", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="artifactreview",
            index=models.Index(fields=["operator", "source_artifact_id"], name="artifact_op_artifact_idx"),
        ),
        migrations.AddIndex(
            model_name="factcorrection",
            index=models.Index(fields=["operator", "source_artifact_id", "fact_key"], name="factcor_op_factkey_idx"),
        ),
        migrations.AddIndex(
            model_name="sourcestance",
            index=models.Index(fields=["operator", "source"], name="stance_op_source_idx"),
        ),
        migrations.AddConstraint(
            model_name="artifactreview",
            constraint=models.CheckConstraint(
                condition=models.Q(("artifact_review_state__in", ["accepted", "disputed", "stale"])),
                name="artifactreview_valid_state",
            ),
        ),
        migrations.AddConstraint(
            model_name="factcorrection",
            constraint=models.CheckConstraint(
                condition=models.Q(("correction_state__in", ["corrected", "disputed", "stale"])),
                name="factcorrection_valid_state",
            ),
        ),
        migrations.AddConstraint(
            model_name="sourcestance",
            constraint=models.CheckConstraint(
                condition=models.Q(("stance__in", ["trusted", "untrusted"])), name="sourcestance_valid_stance"
            ),
        ),
    ]
