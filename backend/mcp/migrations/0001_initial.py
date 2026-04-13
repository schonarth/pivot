# Generated migration for MCP models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otps', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'mcp_otps',
            },
        ),
        migrations.CreateModel(
            name='AgentToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(editable=False, max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('origin', models.CharField(help_text='Agent origin/identifier', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'mcp_agent_tokens',
                'unique_together': {('user', 'origin')},
            },
        ),
        migrations.AddIndex(
            model_name='otp',
            index=models.Index(fields=['user', 'code'], name='mcp_otps_user_id_code_idx'),
        ),
    ]
