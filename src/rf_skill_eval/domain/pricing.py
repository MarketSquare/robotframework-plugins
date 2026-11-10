"""Provider-priced cost for non-Claude models (openrouter-ci-eval-tier D3).

Claude Code prices every session as if it ran on Claude, so its
``total_cost_usd`` is meaningless for an OpenRouter model (the spike reported
$29.66 for $0.84 of real spend). For those runs the harness prices the
reported token counts itself, from OpenRouter's list prices.

List prices are an upper bound: OpenRouter may route a request to a cheaper
host. The figure that counts is the key's spend, which CI reads from
OpenRouter before and after a job.
"""

from __future__ import annotations

from dataclasses import dataclass

from .task import DEEPSEEK_FLASH_MODEL


@dataclass(frozen=True)
class TokenPrices:
    """USD per million tokens."""

    input: float
    cache_read: float
    cache_write: float
    output: float


#: OpenRouter list prices, checked 2026-11-10 (``GET /api/v1/models``).
#: Every id in ``task.OPENROUTER_MODELS`` needs an entry here.
PROVIDER_PRICES: dict[str, TokenPrices] = {
    DEEPSEEK_FLASH_MODEL: TokenPrices(input=0.30, cache_read=0.006, cache_write=0.30, output=1.20),
}


def priced_cost(
    model: str,
    *,
    input_tokens: int,
    cache_read_input_tokens: int,
    cache_creation_input_tokens: int,
    output_tokens: int,
) -> float:
    """Cost in USD of one session's tokens at ``model``'s list prices."""
    p = PROVIDER_PRICES[model]
    return (
        input_tokens * p.input
        + cache_read_input_tokens * p.cache_read
        + cache_creation_input_tokens * p.cache_write
        + output_tokens * p.output
    ) / 1_000_000
