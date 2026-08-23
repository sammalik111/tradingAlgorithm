from functools import lru_cache

from anthropic import AsyncAnthropic

from trading_backend.config import get_settings


class ClaudeNotConfiguredError(RuntimeError):
    """Raised when a Claude call is attempted without an API key configured."""


@lru_cache
def get_claude_client() -> AsyncAnthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ClaudeNotConfiguredError(
            "ANTHROPIC_API_KEY is not set; configure it in Secrets Manager / .env "
            "before requesting recommendation rationale."
        )
    return AsyncAnthropic(api_key=settings.anthropic_api_key)
