# TokenCompress AI

TokenCompress AI is a local token optimization engine for code and prompts. It uses deterministic algorithms instead of external AI APIs:

- AST-based Python code compression removes docstrings and comments while preserving executable semantics.
- Greedy fractional-knapsack compression ranks prompt sentences by information density and keeps only the most valuable units inside a token budget.
- Token telemetry estimates token counts and calculates cost savings using a standard API pricing assumption.

## Features

- Python 3.10+ project structure
- CLI for code and text compression
- Streamlit dashboard with raw vs compressed comparisons
- Unit tests for syntax preservation and budget adherence

## Install

```bash
python -m pip install -r requirements.txt
```

## Run the CLI

Code mode:

```bash
python main.py -f example.py -m code -o compressed.py
```

Text mode:

```bash
python main.py -f sample_prompt.txt -m text -t 250 -o compressed_prompt.txt
```

## Run the dashboard

```bash
python -m streamlit run app.py
```

## Hackathon pitch

TokenCompress AI reduces prompt and code size deterministically, locally, and without external AI calls. It preserves semantics while cutting token spend and improving performance for constrained AI workflows.
