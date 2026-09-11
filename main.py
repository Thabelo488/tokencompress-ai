"""Command-line interface for TokenCompress AI."""

import argparse
from pathlib import Path
from typing import List, Optional

from engine.ast_compressor import compress_python_code
from engine.knapsack_compressor import compress_prompt
from engine.token_counter import calculate_cost_savings, estimate_tokens


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Deterministic LLM token optimizer")
    parser.add_argument("--file", "-f", required=True, type=Path, help="Input source or prompt file")
    parser.add_argument("--mode", "-m", choices=("code", "text"), required=True)
    parser.add_argument("--max-tokens", "-t", type=int, default=250)
    parser.add_argument("--output", "-o", type=Path, help="Optional output path")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run the CLI and return a process exit code."""
    args = build_parser().parse_args(argv)
    source = args.file.read_text(encoding="utf-8")
    compressed = (
        compress_python_code(source)
        if args.mode == "code"
        else compress_prompt(source, args.max_tokens)
    )
    if args.output:
        args.output.write_text(compressed, encoding="utf-8")
    else:
        print(compressed)
    original_tokens = estimate_tokens(source)
    compressed_tokens = estimate_tokens(compressed)
    savings, percentage = calculate_cost_savings(original_tokens, compressed_tokens)
    print(
        f"\nTokens: {original_tokens} -> {compressed_tokens} | "
        f"saved: {percentage:.1f}% (${savings:.6f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
