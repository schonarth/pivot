from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0002_rename_ai_costs_ai_auth_id_created_at_idx_ai_costs_ai_auth_15cf95_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiauth",
            name="task_models",
            field=models.JSONField(blank=True, default=dict, help_text="Task-specific model overrides: {task_type: model_name}"),
        ),
        migrations.AlterField(
            model_name="aiauth",
            name="provider_name",
            field=models.CharField(choices=[("openai", "OpenAI"), ("anthropic", "Anthropic"), ("google", "Google")], default="openai", max_length=20),
        ),
    ]
