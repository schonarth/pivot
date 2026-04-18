from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0003_aiauth_task_models_alter_aiauth_provider_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIInstanceKey",
            fields=[
                ("id", models.SmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                (
                    "provider_name",
                    models.CharField(
                        choices=[("openai", "OpenAI"), ("anthropic", "Anthropic"), ("google", "Google")],
                        default="openai",
                        max_length=20,
                    ),
                ),
                ("api_key_encrypted", models.BinaryField(blank=True, null=True)),
                ("allow_other_users", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "db_table": "ai_instance_keys",
            },
        ),
    ]
