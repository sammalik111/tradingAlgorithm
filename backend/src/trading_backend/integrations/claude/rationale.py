from dataclasses import dataclass

from trading_backend.algorithms.scoring import TickerScore
from trading_backend.config import get_settings
from trading_backend.integrations.claude.client import get_claude_client

SYSTEM_PROMPT = (
    "You summarize publicly disclosed politician stock trades into a short, "
    "neutral rationale for a retail research tool. State only what the "
    "disclosed trades support. Never give personalized financial advice, "
    "never guarantee outcomes, and keep the response under 80 words."
)


@dataclass(frozen=True)
class SupportingTradeSummary:
    politician_name: str
    direction: str
    transaction_date: str
    amount_range: str


def _build_user_prompt(score: TickerScore, trades: list[SupportingTradeSummary]) -> str:
    trade_lines = "\n".join(
        f"- {t.politician_name}: {t.direction.upper()} {score.ticker} on "
        f"{t.transaction_date}, disclosed range {t.amount_range}"
        for t in trades
    )
    return (
        f"Ticker: {score.ticker}\n"
        f"Computed signal: {score.direction.value.upper()} "
        f"(score={score.signal_score:.2f}, conviction={score.conviction.value})\n"
        f"{score.agreeing_politicians} of {score.total_politicians} tracked politicians "
        f"with recent activity agree on this direction.\n\n"
        f"Supporting disclosed trades:\n{trade_lines}\n\n"
        "Write the rationale."
    )


async def generate_rationale(
    score: TickerScore,
    trades: list[SupportingTradeSummary],
) -> str:
    """Turn a computed `TickerScore` and its supporting trades into a short
    natural-language rationale via the Claude API.
    """
    settings = get_settings()
    client = get_claude_client()
    response = await client.messages.create(
        model=settings.recommendation_model,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(score, trades)}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
