import django.db.models.deletion
import uuid
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portfolios", "0003_portfolio_is_simulating"),
    ]

    operations = [
        migrations.CreateModel(
            name="PortfolioGuardrails",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("max_trades_per_day", models.IntegerField(default=10, help_text="Maximum trades allowed per day")),
                ("max_position_size_pct", models.DecimalField(decimal_places=2, default=Decimal("20"), help_text="Max position size as % of portfolio", max_digits=5)),
                ("stop_loss_pct", models.DecimalField(decimal_places=2, default=Decimal("-5"), help_text="Stop loss threshold as % change from entry", max_digits=5)),
                ("take_profit_pct", models.DecimalField(decimal_places=2, default=Decimal("10"), help_text="Take profit threshold as % change from entry", max_digits=5)),
                ("min_order_value", models.DecimalField(decimal_places=2, default=Decimal("10"), help_text="Minimum order value in portfolio currency", max_digits=20)),
                ("enabled", models.BooleanField(default=False, help_text="Enable guardrails enforcement")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("portfolio", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="guardrails", to="portfolios.portfolio")),
            ],
            options={
                "db_table": "portfolio_guardrails",
            },
        ),
    ]
