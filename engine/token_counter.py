"""Token estimation and cost telemetry with an optional tiktoken backend."""

from typing import Optional, Tuple

try:
    import tiktoken
except ImportError:  # pragma: no cover - exercised when optional dependency is absent
    tiktoken = None


def estimate_tokens(text: str, encoding_name: Optional[str] = None) -> int:
    """Estimate tokens using tiktoken when available, otherwise four chars/token."""
    if not text:
        return 0
    if tiktoken is not None:
        try:
            encoding = (
                tiktoken.get_encoding(encoding_name)
                if encoding_name
                else tiktoken.get_encoding("cl100k_base")
            )
            return len(encoding.encode(text))
        except (KeyError, ValueError, RuntimeError):
            pass
    return max(1, (len(text) + 3) // 4)


def calculate_cost_savings(
    original_tokens: int,
    compressed_tokens: int,
    price_per_million: float = 3.00,
) -> Tuple[float, float]:
    """Return saved dollars and percentage reduction for one input."""
    original = max(0, original_tokens)
    compressed = min(max(0, compressed_tokens), original)
    saved_tokens = original - compressed
    savings = saved_tokens / 1_000_000 * max(0.0, price_per_million)
    percentage = (saved_tokens / original * 100.0) if original else 0.0
    return savings, percentage
