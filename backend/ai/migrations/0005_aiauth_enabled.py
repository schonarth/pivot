from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0004_aiinstancekey"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiauth",
            name="enabled",
            field=models.BooleanField(default=True),
        ),
    ]
