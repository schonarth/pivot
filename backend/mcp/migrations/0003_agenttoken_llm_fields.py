from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mcp', '0002_rename_mcp_otps_user_id_code_idx_mcp_otps_user_id_3b8518_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='agenttoken',
            name='llm_provider',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='agenttoken',
            name='llm_model',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]
