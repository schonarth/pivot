from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai", "0006_strategyrecommendation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="strategyrecommendation",
            name="rationale",
            field=models.TextField(),
        ),
    ]
