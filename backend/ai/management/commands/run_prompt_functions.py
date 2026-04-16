from django.core.management.base import BaseCommand, CommandError

from ai.models import TASK_MODELS
from ai.services import AIService
from markets.models import Asset, NewsItem, TechnicalIndicators


class Command(BaseCommand):
    # Diagnostic command: runs each prompt-bearing AI path and prints the exact
    # prompt, model, and raw model response so prompt quality can be inspected.
    help = "Run backend prompt-bearing AI functions and print a simple report."

    def add_arguments(self, parser):
        # Usage:
        #   docker compose exec backend python manage.py run_prompt_functions <api_key> --symbol AAPL
        parser.add_argument("api_key")
        parser.add_argument("--provider", default="openai")
        parser.add_argument("--asset-id")
        parser.add_argument("--symbol")
        parser.add_argument("--headlines-limit", type=int, default=5)

    def handle(self, *args, **options):
        provider = options["provider"]
        api_key = options["api_key"].strip()

        asset = self._get_asset(options["asset_id"], options["symbol"])
        indicators = self._get_indicators(asset)
        context_items = self._get_news_items(asset)
        headlines = self._get_headlines(options["headlines_limit"])

        reports = [
            self._run_connection_test(provider, api_key),
            self._run_asset_insight(provider, api_key, asset, indicators, context_items),
            self._run_sentiment_analysis(provider, api_key, headlines),
        ]

        for report in reports:
            self.stdout.write(f"Function: {report['function']}")
            self.stdout.write(f"Model: {report['model']}")
            self.stdout.write("Prompt:")
            self.stdout.write(report["prompt"])
            self.stdout.write("Response:")
            self.stdout.write(report["response_text"])
            self.stdout.write("")

    def _get_asset(self, asset_id, symbol):
        if asset_id:
            return Asset.objects.get(id=asset_id)
        if symbol:
            asset = Asset.objects.filter(display_symbol=symbol).first()
            if asset:
                return asset
            raise CommandError(f"No asset found for symbol {symbol}")
        preferred = Asset.objects.filter(display_symbol="AAPL").first()
        if preferred:
            return preferred
        asset = Asset.objects.order_by("market", "display_symbol").first()
        if not asset:
            raise CommandError("No assets available")
        return asset

    def _get_indicators(self, asset):
        indicators = TechnicalIndicators.objects.filter(asset=asset).order_by("-date").first()
        if not indicators:
            raise CommandError(f"No indicators available for {asset.display_symbol}")
        return {
            "rsi_14": indicators.rsi_14,
            "macd": indicators.macd,
            "macd_signal": indicators.macd_signal,
            "macd_histogram": indicators.macd_histogram,
            "ma_20": indicators.ma_20,
            "ma_50": indicators.ma_50,
            "ma_200": indicators.ma_200,
            "bb_upper": indicators.bb_upper,
            "bb_middle": indicators.bb_middle,
            "bb_lower": indicators.bb_lower,
            "volume_20d_avg": indicators.volume_20d_avg,
        }

    def _get_news_items(self, asset):
        return AIService.build_asset_context_pack(asset)

    def _get_headlines(self, limit):
        return list(
            NewsItem.objects.filter(sentiment_score__isnull=True)
            .order_by("-fetched_at")
            .values_list("headline", flat=True)[:limit]
        )

    def _run_connection_test(self, provider, api_key):
        model = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-haiku-4-5-20251001",
            "google": "gemini-2.0-flash",
        }.get(provider, "gpt-4o-mini")
        prompt = AIService.build_connection_test_prompt()
        response = AIService.test_connection(provider=provider, api_key=api_key, model=model)
        return {
            "function": "AIService.test_connection",
            "model": response["model"],
            "prompt": prompt,
            "response_text": response["message"],
        }

    def _run_asset_insight(self, provider, api_key, asset, indicators, news_items):
        model = TASK_MODELS["indicator_insight"].get(provider, "gpt-4o-mini")
        prompt = AIService.build_indicator_insight_prompt(asset, indicators, news_items)
        response_text = self._call_provider(provider, api_key, model, prompt, max_output_tokens=300)
        return {
            "function": "AIService.analyze_asset",
            "model": model,
            "prompt": prompt,
            "response_text": response_text,
        }

    def _run_sentiment_analysis(self, provider, api_key, headlines):
        if not headlines:
            return {
                "function": "AIService.analyze_news_sentiment",
                "model": TASK_MODELS["sentiment_analysis"].get(provider, "gpt-4o-mini"),
                "prompt": "No headlines available",
                "response_text": "",
            }
        model = TASK_MODELS["sentiment_analysis"].get(provider, "gpt-4o-mini")
        prompt = AIService.build_sentiment_prompt(headlines)
        response_text = self._call_provider(provider, api_key, model, prompt, max_output_tokens=500)
        return {
            "function": "AIService.analyze_news_sentiment",
            "model": model,
            "prompt": prompt,
            "response_text": response_text,
        }

    def _call_provider(self, provider, api_key, model, prompt, max_output_tokens):
        if provider == "openai":
            import openai

            response = openai.OpenAI(api_key=api_key).responses.create(
                model=model,
                max_output_tokens=max_output_tokens,
                input=prompt,
            )
            return response.output_text

        if provider == "anthropic":
            import anthropic

            message = anthropic.Anthropic(api_key=api_key).messages.create(
                model=model,
                max_tokens=max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text if message.content else ""

        if provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            response = genai.GenerativeModel(model).generate_content(prompt)
            return response.text

        raise CommandError(f"Unsupported provider: {provider}")
