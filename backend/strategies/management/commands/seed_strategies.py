from django.core.management.base import BaseCommand
from strategies.models import StrategyRule


class Command(BaseCommand):
    help = "Seed predefined strategy rules"

    def handle(self, *args, **options):
        rules = [
            {
                "name": "RSI Oversold/Overbought",
                "rule_type": "rsi_oversold",
                "description": "Buy when RSI crosses above 30 (oversold), sell when crosses below 70 (overbought)",
                "conditions": {
                    "rsi_length": 14,
                    "oversold_threshold": 30,
                    "overbought_threshold": 70,
                }
            },
            {
                "name": "MA 20/50 Crossover",
                "rule_type": "ma_crossover",
                "description": "Buy when 20-day MA crosses above 50-day MA, sell when crosses below",
                "conditions": {
                    "fast_ma": 20,
                    "slow_ma": 50,
                }
            },
            {
                "name": "MACD Crossover",
                "rule_type": "macd_crossover",
                "description": "Buy when MACD crosses above signal line, sell when crosses below",
                "conditions": {
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9,
                }
            },
            {
                "name": "Bollinger Bands",
                "rule_type": "bb_bands",
                "description": "Buy when price touches lower band, sell when price touches upper band",
                "conditions": {
                    "bb_period": 20,
                    "bb_std_dev": 2,
                }
            },
        ]

        for rule_data in rules:
            rule, created = StrategyRule.objects.get_or_create(
                rule_type=rule_data["rule_type"],
                defaults={
                    "name": rule_data["name"],
                    "description": rule_data["description"],
                    "conditions": rule_data["conditions"],
                }
            )
            status = "Created" if created else "Already exists"
            self.stdout.write(self.style.SUCCESS(f"{status}: {rule.name}"))
