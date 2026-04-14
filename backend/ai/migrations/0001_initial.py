# Generated migration for AIAuth and AICost models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AIAuth',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('provider_name', models.CharField(choices=[('openai', 'OpenAI'), ('anthropic', 'Anthropic')], default='openai', max_length=20)),
                ('api_key_encrypted', models.BinaryField(blank=True, null=True)),
                ('monthly_budget_usd', models.DecimalField(decimal_places=2, default='10.00', help_text='Monthly budget in USD for AI calls', max_digits=8)),
                ('alert_threshold_pct', models.IntegerField(default=10, help_text='Warn when this % of budget remains (e.g., 10 = warn at 90% consumed)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ai_auth', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ai_auth',
            },
        ),
        migrations.CreateModel(
            name='AICost',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('model_name', models.CharField(max_length=100)),
                ('prompt_tokens', models.IntegerField(default=0)),
                ('completion_tokens', models.IntegerField(default=0)),
                ('cost_usd', models.DecimalField(decimal_places=6, max_digits=10)),
                ('task_type', models.CharField(help_text="Type of task (e.g., 'asset_filtering', 'indicator_insight', 'trade_validation')", max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ai_auth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='costs', to='ai.aiauth')),
            ],
            options={
                'db_table': 'ai_costs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='aicost',
            index=models.Index(fields=['ai_auth', '-created_at'], name='ai_costs_ai_auth_id_created_at_idx'),
        ),
    ]
