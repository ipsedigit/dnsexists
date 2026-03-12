---
title: Python Project Init — dnsexists
date: 2026-03-12
card: DEV-7
---

# Design: Initialize dnsexists as a Python Project

## Summary

Initialize the `dnsexists` repository as a minimal Python CLI tool using a flat single-module layout. No packaging, no build backend — the tool is run directly.

## Layout

```
dnsexists/
├── dnsexists.py          # single module: DNS logic + CLI entry point
├── requirements.txt      # runtime dependencies (empty — stdlib only)
├── requirements-dev.txt  # dev dependencies: pytest
├── tests/                # pytest test files
│   └── test_dnsexists.py
└── README.md             # existing file
```

## Architecture

- **`dnsexists.py`** — single file containing all logic and a `main()` function as the CLI entry point. Invoked via `python dnsexists.py` or `python -m dnsexists`.
- **DNS resolution** — uses Python's stdlib `socket` module; no external runtime dependencies.
- **Testing** — `pytest` in `requirements-dev.txt`; tests live in a `tests/` directory.

## Constraints

- Python 3.12
- `pip` + `requirements.txt` (no uv, poetry, or other tooling)
- No `pyproject.toml` — tool is not installed as a package
- No `src/` layout
