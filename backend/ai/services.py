import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum
from django.utils import timezone

from .models import AIAuth, AICost
from .encryption import KeyEncryption

logger = logging.getLogger("paper_trader.ai")


class AIBudgetError(Exception):
    """Raised when AI budget limit is exceeded."""
    pass


class AIService:
    """Manage AI API calls with budget enforcement and usage tracking."""

    def __init__(self, user):
        self.user = user
        self.ai_auth = AIAuth.objects.filter(user=user).first()

    def has_ai_enabled(self) -> bool:
        """Check if user has AI enabled (has API key configured)."""
        return self.ai_auth is not None and self.ai_auth.api_key_encrypted is not None

    def get_monthly_usage_usd(self) -> Decimal:
        """Get total usage for current month in USD."""
        if not self.ai_auth:
            return Decimal("0")

        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total = AICost.objects.filter(
            ai_auth=self.ai_auth,
            created_at__gte=month_start
        ).aggregate(total=Sum("cost_usd"))["total"]

        return total or Decimal("0")

    def get_monthly_budget_usd(self) -> Decimal:
        """Get monthly budget in USD."""
        if not self.ai_auth:
            return Decimal("0")
        return self.ai_auth.monthly_budget_usd

    def get_remaining_budget_usd(self) -> Decimal:
        """Get remaining budget for this month in USD."""
        budget = self.get_monthly_budget_usd()
        usage = self.get_monthly_usage_usd()
        return max(Decimal("0"), budget - usage)

    def get_budget_percentage_used(self) -> Decimal:
        """Get percentage of monthly budget used (0-100)."""
        budget = self.get_monthly_budget_usd()
        if budget == 0:
            return Decimal("0")
        usage = self.get_monthly_usage_usd()
        return (usage / budget) * 100

    def is_at_budget_limit(self) -> bool:
        """Check if budget limit has been reached."""
        return self.get_remaining_budget_usd() <= 0

    def should_warn(self) -> bool:
        """Check if usage warning should be shown."""
        if not self.ai_auth:
            return False
        pct_used = self.get_budget_percentage_used()
        warn_threshold = 100 - self.ai_auth.alert_threshold_pct
        return pct_used >= warn_threshold

    def check_budget(self) -> None:
        """Raise error if budget limit exceeded."""
        if self.is_at_budget_limit():
            raise AIBudgetError(
                f"AI budget limit reached. "
                f"${self.get_monthly_usage_usd():.2f} of "
                f"${self.get_monthly_budget_usd():.2f} spent this month."
            )

    def log_call(self, model_name: str, prompt_tokens: int, completion_tokens: int,
                 cost_usd: Decimal, task_type: str) -> AICost:
        """Log an AI API call and its cost."""
        if not self.ai_auth:
            raise ValueError("No AI auth configured for this user")

        cost = AICost.objects.create(
            ai_auth=self.ai_auth,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            task_type=task_type,
        )

        logger.info(
            f"AI call logged: {self.user.username} - {model_name} - "
            f"{prompt_tokens}p+{completion_tokens}c - ${cost_usd} - {task_type}"
        )

        return cost

    def get_api_key(self) -> str | None:
        """Get decrypted API key for current provider."""
        if not self.ai_auth or not self.ai_auth.api_key_encrypted:
            return None
        try:
            return KeyEncryption.decrypt(self.ai_auth.api_key_encrypted)
        except Exception as e:
            logger.exception(f"Failed to decrypt API key for {self.user.username}: {e}")
            return None

    def set_api_key(self, api_key: str) -> None:
        """Store encrypted API key."""
        if not self.ai_auth:
            self.ai_auth = AIAuth.objects.create(user=self.user)

        self.ai_auth.api_key_encrypted = KeyEncryption.encrypt(api_key)
        self.ai_auth.save()
        logger.info(f"API key updated for {self.user.username}")

    def clear_api_key(self) -> None:
        """Remove API key."""
        if self.ai_auth:
            self.ai_auth.api_key_encrypted = None
            self.ai_auth.save()
            logger.info(f"API key removed for {self.user.username}")

    def get_budget_info(self) -> dict:
        """Get budget info for display in header/settings."""
        pct_used = self.get_budget_percentage_used()
        return {
            "enabled": self.has_ai_enabled(),
            "monthly_budget_usd": str(self.get_monthly_budget_usd()),
            "usage_usd": str(self.get_monthly_usage_usd()),
            "remaining_usd": str(self.get_remaining_budget_usd()),
            "percentage_used": f"{pct_used:.0f}",
            "at_limit": self.is_at_budget_limit(),
            "should_warn": self.should_warn(),
        }
