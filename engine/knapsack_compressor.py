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
_STRUCTURE_WEIGHTS: Dict[str, float] = {
    "instruction": 2.0,
    "constraint": 2.4,
    "output": 2.2,
    "context": 1.4,
    "example": 1.1,
    "filler": 0.1,
}


@dataclass(frozen=True)
class PromptUnit:
    """A selectable prompt unit and its deterministic scoring metadata."""

    index: int
    text: str
    weight: int
    value: float
    category: str


def classify_unit(text: str) -> str:
    """Classify a unit using deterministic linguistic and formatting cues."""
    lowered = text.lower()
    if any(marker in lowered for marker in ("must ", "never ", "always ", "required", "do not")):
        return "constraint"
    if any(marker in lowered for marker in ("return ", "output", "format", "respond", "include")):
        return "output"
    if any(marker in lowered for marker in ("for example", "e.g.", "example:", "```")):
        return "example"
    if any(marker in lowered for marker in ("input", "context", "background", "given ", "the user")):
        return "context"
    if any(marker in lowered for marker in ("please", "thank you", "hello", "kindly")):
        return "filler"
    return "instruction"


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
    scored: List[PromptUnit] = []
    for index, unit in enumerate(split_prompt_units(text)):
        category = classify_unit(unit)
        value = information_density(unit) + _STRUCTURE_WEIGHTS[category]
        scored.append(
            PromptUnit(
                index=index,
                text=unit,
                weight=estimate_tokens(unit),
                value=value,
                category=category,
            )
        )
    return scored


def _similarity(left: str, right: str) -> float:
    """Return token-set Jaccard similarity for redundancy detection."""
    left_words = set(re.findall(r"[a-z][a-z'-]+", left.lower()))
    right_words = set(re.findall(r"[a-z][a-z'-]+", right.lower()))
    union = left_words | right_words
    return len(left_words & right_words) / len(union) if union else 0.0


def _select_units(units: List[PromptUnit], max_tokens: int) -> List[PromptUnit]:
    """Select a high-value, non-redundant subset with exact 0/1 knapsack DP."""
    if not units or max_tokens <= 0:
        return []
    # Account for newline separators so the final rendered prompt stays bounded.
    weights = [unit.weight + 1 for unit in units]
    values = [unit.value for unit in units]
    dp: List[float] = [0.0] * (max_tokens + 1)
    choices: List[List[int]] = [[] for _ in range(max_tokens + 1)]
    for index, unit in enumerate(units):
        weight = weights[index]
        if weight > max_tokens:
            continue
        for budget in range(max_tokens, weight - 1, -1):
            previous = choices[budget - weight]
            if any(_similarity(unit.text, units[item].text) >= 0.75 for item in previous):
                continue
            candidate = dp[budget - weight] + values[index]
            if candidate > dp[budget]:
                dp[budget] = candidate
                choices[budget] = previous + [index]
    selected = [units[index] for index in choices[max_tokens]]
    selected.sort(key=lambda unit: unit.index)
    return selected


def compress_prompt(text: str, max_tokens: int) -> str:
    """Select structured, high-value complete units within ``max_tokens``."""
    if max_tokens <= 0 or not text.strip():
        return ""
    units = score_prompt_units(text)
    selected = _select_units(units, max_tokens)
    output = "\n".join(unit.text for unit in selected)
    # A tokenizer can count separators differently; trim lowest-value units if needed.
    while estimate_tokens(output) > max_tokens and selected:
        selected.pop()
        output = "\n".join(unit.text for unit in selected)
    return output


def compression_stats(text: str, max_tokens: int) -> Dict[str, int]:
    """Return source, compressed, and budget token counts for a prompt."""
    compressed = compress_prompt(text, max_tokens)
    return {
        "original_tokens": estimate_tokens(text),
        "compressed_tokens": estimate_tokens(compressed),
        "budget": max(0, max_tokens),
    }
