import random
import string
import secrets
from typing import Optional
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from .models import OTP, AgentToken


def generate_otp(user: User) -> str:
    """Generate a 6-digit OTP valid for 1 minute."""
    code = ''.join(random.choices(string.digits, k=6))
    otp = OTP.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=1)
    )
    return code


def validate_and_use_otp(user: User, code: str) -> bool:
    """Validate and mark OTP as used. Returns True if valid."""
    try:
        otp = OTP.objects.get(user=user, code=code)
        if not otp.is_valid():
            return False
        otp.mark_used()
        return True
    except OTP.DoesNotExist:
        return False


def generate_agent_token(user: User, name: str, origin: str, llm_provider: str = '', llm_model: str = '') -> str:
    """Generate and store an agent token."""
    token = secrets.token_urlsafe(32)
    AgentToken.objects.update_or_create(
        user=user,
        origin=origin,
        defaults={
            'token': token,
            'name': name,
            'llm_provider': llm_provider,
            'llm_model': llm_model,
        }
    )
    return token


def verify_agent_token(token: str) -> Optional[User]:
    """Verify agent token and return user. Updates last_used_at."""
    try:
        agent_token = AgentToken.objects.get(token=token)
        agent_token.last_used_at = timezone.now()
        agent_token.save(update_fields=['last_used_at'])
        return agent_token.user
    except AgentToken.DoesNotExist:
        return None
