# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core commands

```bash
# Create virtual env (if needed) and activate
python3 -m venv .venv
source .venv/bin/activate   # Windows → .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run full test suite
pytest

# Run a single test (replace `TestClass.test_method` with actual name)
pytest -k "TestClass::test_method"
```

## High‑level structure

```
free‑run‑claude/
├─ src/            # Python source modules
├─ tests/          # Unit tests against src
├─ test.py         # Stand‑alone script, crawls Yahoo Finance
├─ requirements.txt
└─ README.md
```

`test.py` is a small utility that fetches the latest closing price for a given ticker (default `2330.TW`). It uses only the standard library, providing a fall‑back price when network or API errors occur. Unit tests in `tests/` exercise this logic.

## Typical workflow

1. **Develop** – Add Python modules in `src/`.
2. **Test** – Run `pytest` to validate changes; use `-k` for targeted tests.
3. **Run utility** – Execute `test.py` directly: `python test.py`.

## Notes

- No build step is required; the repo is pure Python.
- Linting or type‑checking is not configured; focus on functionality and tests.
- The environment is assumed to be Python 3.9+.

```
