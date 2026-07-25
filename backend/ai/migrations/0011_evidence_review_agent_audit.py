import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0010_recommendationinvalidation"),
        ("mcp", "0003_agenttoken_llm_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="factcorrection",
            name="created_by_agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_fact_corrections",
                to="mcp.agenttoken",
            ),
        ),
        migrations.AddField(
            model_name="factcorrection",
            name="superseded_by_agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="superseded_fact_corrections",
                to="mcp.agenttoken",
            ),
        ),
        migrations.AddField(
            model_name="artifactreview",
            name="created_by_agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_artifact_reviews",
                to="mcp.agenttoken",
            ),
        ),
        migrations.AddField(
            model_name="artifactreview",
            name="superseded_by_agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="superseded_artifact_reviews",
                to="mcp.agenttoken",
            ),
        ),
        migrations.AddField(
            model_name="sourcestance",
            name="created_by_agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_source_stances",
                to="mcp.agenttoken",
            ),
        ),
        migrations.AddField(
            model_name="sourcestance",
            name="superseded_by_agent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="superseded_source_stances",
                to="mcp.agenttoken",
            ),
        ),
    ]
