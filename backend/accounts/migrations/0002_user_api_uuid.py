# Generated migration for adding api_uuid field

import uuid
from django.db import migrations, models


def populate_api_uuid(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        if not user.api_uuid:
            user.api_uuid = uuid.uuid4()
            user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='api_uuid',
            field=models.UUIDField(editable=False, null=True, blank=True),
        ),
        migrations.RunPython(populate_api_uuid),
        migrations.AlterField(
            model_name='user',
            name='api_uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
