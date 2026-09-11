"""Deterministic information-density prompt compression."""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .token_counter import estimate_tokens

_HIGH_VALUE_KEYWORDS: Tuple[str, ...] = (
    "must",
    "always",
    "never",
    "return",
    "error",
    "class",
    "function",
    "require",
    "should",
    "input",
    "output",
)
_LOW_VALUE_KEYWORDS: Tuple[str, ...] = (
    "please",
    "thank you",
    "hello",
    "kindly",
    "would you",
    "could you",
)


@dataclass(frozen=True)
class PromptUnit:
    """A selectable prompt unit and its deterministic scoring metadata."""

    index: int
    text: str
    weight: int
    value: float


def split_prompt_units(text: str) -> List[str]:
    """Split prompts into non-empty lines or sentence-like units."""
    units: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        pieces = re.split(r"(?<=[.!?])\s+", stripped)
        units.extend(piece.strip() for piece in pieces if piece.strip())
    return units


def information_density(text: str) -> float:
    """Score directives and technical terms above conversational language."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text.lower())
    score = 1.0 + min(len(words), 40) * 0.02
    lowered = text.lower()
    score += sum(2.5 for keyword in _HIGH_VALUE_KEYWORDS if keyword in words)
    score -= sum(1.0 for keyword in _LOW_VALUE_KEYWORDS if keyword in lowered)
    if any(character in text for character in (":", ";", "=", "`")):
        score += 0.75
    return max(score, 0.1)


def score_prompt_units(text: str) -> List[PromptUnit]:
    """Return prompt units with estimated token weights and density values."""
    return [
        PromptUnit(index=index, text=unit, weight=estimate_tokens(unit), value=information_density(unit))
        for index, unit in enumerate(split_prompt_units(text))
    ]


def compress_prompt(text: str, max_tokens: int) -> str:
    """Select the densest complete units that fit within ``max_tokens``.

    This is the practical whole-unit variant of a greedy fractional knapsack:
    units are ranked by value/weight, while output remains readable and never
    exceeds the requested budget.
    """
    if max_tokens <= 0 or not text.strip():
        return ""
    units = score_prompt_units(text)
    ranked = sorted(
        units,
        key=lambda unit: (unit.value / max(unit.weight, 1), unit.value, -unit.index),
        reverse=True,
    )
    selected: List[PromptUnit] = []
    used_tokens = 0
    for unit in ranked:
        if used_tokens + unit.weight <= max_tokens:
            selected.append(unit)
            used_tokens += unit.weight
    selected.sort(key=lambda unit: unit.index)
    return "\n".join(unit.text for unit in selected)


def compression_stats(text: str, max_tokens: int) -> Dict[str, int]:
    """Return source, compressed, and budget token counts for a prompt."""
    compressed = compress_prompt(text, max_tokens)
    return {
        "original_tokens": estimate_tokens(text),
        "compressed_tokens": estimate_tokens(compressed),
        "budget": max(0, max_tokens),
    }
