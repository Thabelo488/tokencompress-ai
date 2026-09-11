"""Streamlit dashboard for TokenCompress AI."""

from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st

from engine.ast_compressor import compress_python_code
from engine.knapsack_compressor import compress_prompt
from engine.token_counter import calculate_cost_savings, estimate_tokens


def build_demo_examples() -> List[Dict[str, str]]:
    """Return a few ready-made examples for the hackathon demo."""
    return [
        {
            "title": "Code cleanup",
            "mode": "code",
            "content": '"""module docs"""\n# no-op comment\nVALUE = 5\n\ndef sum_items(items):\n    """sum items"""\n    total = 0\n    for item in items:\n        total += item\n    return total\n',
        },
        {
            "title": "Prompt compression",
            "mode": "text",
            "content": "Hello, please help me. The function must return an error for invalid input. Thank you for your assistance.",
        },
        {
            "title": "API spec",
            "mode": "text",
            "content": "Always validate input before sending a request. Return the class payload when the response is successful. Never expose secrets in logs or error messages.",
        },
    ]


def summarize_case(raw_text: str, mode: str, max_tokens: int) -> Dict[str, float]:
    """Evaluate one source text against the current compression settings."""
    compressed = compress_python_code(raw_text) if mode == "code" else compress_prompt(raw_text, max_tokens)
    original_tokens = estimate_tokens(raw_text)
    compressed_tokens = estimate_tokens(compressed)
    savings, percentage = calculate_cost_savings(original_tokens, compressed_tokens)
    return {
        "original_tokens": float(original_tokens),
        "compressed_tokens": float(compressed_tokens),
        "savings": float(savings),
        "percentage": float(percentage),
    }


def render() -> None:
    """Render the interactive single-page dashboard."""
    st.set_page_config(page_title="TokenCompress AI", page_icon="⚡", layout="wide")
    st.title("TokenCompress AI")
    st.caption("Deterministic AST and information-density compression for local workflows.")

    st.markdown(
        "<div style='padding: 0.75rem 1rem; border-left: 4px solid #4fd1c5; background: #0e1117; border-radius: 8px;'>"
        "Built for hackathons: local, deterministic, and API-free token optimization for code and prompts."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Controls")
        mode = st.radio("Compression mode", ("code", "text"), horizontal=True)
        max_tokens = st.slider("Target token budget", min_value=1, max_value=2000, value=250)
        uploaded = st.file_uploader("Upload a source or prompt file", type=["py", "txt", "md"])

    default = ""
    if uploaded is not None:
        default = uploaded.getvalue().decode("utf-8")
    source = st.text_area("Input", value=default, height=280)

    compressed = compress_python_code(source) if mode == "code" else compress_prompt(source, max_tokens)
    original_count = estimate_tokens(source)
    compressed_count = estimate_tokens(compressed)
    savings, percentage = calculate_cost_savings(original_count, compressed_count)
    reduction_ratio = (compressed_count / original_count) if original_count else 0.0

    left, right = st.columns(2)
    with left:
        st.subheader("Raw input")
        st.code(source if source else "# Paste code or text here", language="python" if mode == "code" else "text")
        st.metric("Token count", original_count)
    with right:
        st.subheader("Compressed output")
        st.code(compressed if compressed else "# Output will appear here", language="python" if mode == "code" else "text")
        st.metric("Token count", compressed_count)

    metric_left, metric_middle, metric_right = st.columns(3)
    metric_left.metric("% Tokens saved", f"{percentage:.1f}%")
    metric_middle.metric("Total cost savings", f"${savings:.6f}")
    metric_right.metric("Reduction ratio", f"{reduction_ratio:.2f}x")

    if st.button("Save compressed output"):
        output_path = Path("tokencompress_output.py" if mode == "code" else "tokencompress_output.txt")
        output_path.write_text(compressed, encoding="utf-8")
        st.success(f"Saved to {output_path}")

    st.markdown("---")
    st.subheader("Hackathon benchmark snapshots")
    benchmark_columns = st.columns(3)
    for column, case in zip(benchmark_columns, build_demo_examples()):
        with column:
            raw = case["content"]
            stats = summarize_case(raw, case["mode"], max_tokens)
            st.markdown(f"### {case['title']}")
            st.write(f"Raw: {int(stats['original_tokens'])} tokens")
            st.write(f"Compressed: {int(stats['compressed_tokens'])} tokens")
            st.metric("Savings", f"{stats['percentage']:.1f}%")


if __name__ == "__main__":
    render()
