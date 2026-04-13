# Generated migration for adding initiated_by field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashtransaction',
            name='initiated_by',
            field=models.CharField(
                choices=[('user', 'User'), ('agent', 'Agent')],
                default='user',
                max_length=10
            ),
        ),
    ]
