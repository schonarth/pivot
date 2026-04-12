# Generated migration for price_was_override field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='alerttrigger',
            name='price_was_override',
            field=models.BooleanField(default=False),
        ),
    ]
