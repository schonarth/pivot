import json

from django.core.management.base import BaseCommand, CommandError

from ai.services import AIService
from markets.models import Asset


class Command(BaseCommand):
    help = "Inspect deterministic divergence output for an asset or monitored set."

    def add_arguments(self, parser):
        parser.add_argument("--asset-id", action="append", dest="asset_ids")
        parser.add_argument("--symbol", action="append", dest="symbols")
        parser.add_argument(
            "--scope-type",
            choices=["asset", "portfolio", "watch"],
            default="asset",
        )
        parser.add_argument("--scope-label", default="Ad hoc monitored set")

    def handle(self, *args, **options):
        assets = self._get_assets(options["asset_ids"], options["symbols"])
        scope_type = options["scope_type"]
        scope_label = options["scope_label"]

        if scope_type == "asset" and len(assets) > 1:
            assets = assets[:1]

        news_items = AIService.build_scope_context_pack(assets)
        sentiment_trajectory = AIService.build_sentiment_trajectory(
            news_items,
            {asset.display_symbol for asset in assets},
        )
        divergence = AIService.build_divergence_analysis(
            scope_type,
            assets,
            news_items,
            sentiment_trajectory,
        )

        self.stdout.write(f"Scope type: {scope_type}")
        self.stdout.write(f"Scope label: {scope_label}")
        self.stdout.write("Assets:")
        for asset in assets:
            self.stdout.write(f"- {asset.display_symbol} ({asset.market})")
        self.stdout.write("Divergence:")
        self.stdout.write(json.dumps(divergence, indent=2, default=str))
        self.stdout.write("Prompt section:")
        self.stdout.write(AIService.build_divergence_prompt_section(divergence))
        self.stdout.write("Summary:")
        self.stdout.write(AIService.build_divergence_summary(divergence))
        self.stdout.write("Disclosure:")
        self.stdout.write(AIService.build_divergence_disclosure(scope_type))

    def _get_assets(self, asset_ids, symbols):
        asset_ids = asset_ids or []
        symbols = symbols or []

        assets = list(Asset.objects.filter(id__in=asset_ids))
        if symbols:
            assets.extend(Asset.objects.filter(display_symbol__in=symbols))

        if assets:
            unique_assets = []
            seen = set()
            for asset in assets:
                if asset.id in seen:
                    continue
                seen.add(asset.id)
                unique_assets.append(asset)
            return unique_assets

        default_asset = Asset.objects.order_by("market", "display_symbol").first()
        if default_asset:
            return [default_asset]

        raise CommandError("No assets available")
