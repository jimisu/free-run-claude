# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

- **Setup virtual environment**
  ```bash
  python3 -m venv .venv            # create isolated environment
  source .venv/bin/activate         # macOS / Linux
  # Windows: .venv\Scripts\activate
  ```
- **Install dependencies**
  ```bash
  # The repository does not currently ship a requirements.txt, but the script requires the `requests` library.
  pip install requests
  ```
- **Run the script**
  ```bash
  python test.py                     # prints the latest TSMC price (online mode)
  ```
- **Execute a specific function from an interactive session**
  ```bash
  python -c "from test import get_latest_price; print(get_latest_price())"
  ```
- **Lint / format (if added later)** – no linting configuration is present, but you can use a standard tool such as `ruff` or `black` when they are introduced.

## High‑Level Code Architecture

The repository consists of a single entry‑point script **`test.py`** that implements a small, self‑contained utility for retrieving the latest closing price of the TSMC stock (symbol `2330.TW`). The logical layers are:

1. **Dependency handling** – attempts to import `requests`; if unavailable, the script fails early with a clear error.
2. **Network fetch layer (`_fetch_online`)** – builds a Yahoo Finance query URL, performs an HTTP GET with retry logic (`MAX_RETRIES` and `RETRY_DELAY`), validates the response, parses JSON, and extracts the most recent close price.
3. **Public API (`get_latest_price`)** – a thin wrapper that returns a tuple `(price, "online")`. It purposefully propagates any exception so callers can decide how to handle failures (e.g., fallback to a hard‑coded value in “offline” mode).
4. **CLI entry point** – guarded by `if __name__ == "__main__"`, prints the price to stdout on success or an error message to stderr on failure.

Future contributors can extend this architecture by:
- Adding an offline fallback implementation (e.g., returning a cached or hard‑coded price) inside `get_latest_price` when `_fetch_online` raises.
- Splitting the script into a package (e.g., `src/price_fetcher/`) and moving the helper functions there, leaving a lightweight command‑line wrapper in `bin/`.
- Introducing unit tests under a `tests/` directory that mock the network call (`requests.get`) to verify retry and error handling logic.

## Repository Layout Overview

```
.
├─ CLAUDE.md          # (this file) guidance for Claude Code
├─ README.md          # high‑level description and quick‑start
├─ .gitignore         # ignores virtual env and caches
├─ test.py            # main script described above
└─ venv/              # optional local virtual environment (not version‑controlled)
```

No additional source directories (`src/`, `tests/`) exist yet, but the README references them as a conventional layout for future expansion.

---
*When adding new features or files, update this CLAUDE.md to reflect any new commands, architectural changes, or important conventions.*