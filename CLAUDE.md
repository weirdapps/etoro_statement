# etoro_statement

Single-script tool that reads an eToro Excel account statement and outputs a formatted financial summary to the terminal, then saves a CSV alongside the input file.

## Tech Stack

- Python 3.11+ (mypy/ruff target), CI runs 3.12
- pandas, openpyxl, rich
- No build system — `pyproject.toml` is tool config only (ruff, mypy, pytest)
- Lockfile: `requirements-lock.txt` (hashed, pip-compile managed)

## Running

```bash
pip install --require-hashes -r requirements-lock.txt
python etoro_summary.py <path-to-statement.xlsx>
# outputs formatted Rich table to terminal
# saves <input>_summary.csv alongside the xlsx
```

## Testing

```bash
pip install --require-hashes -r requirements-lock.txt
pytest -v
```

## Code Organization

Flat single-script layout — no package structure:

```text
etoro_statement/
├── etoro_summary.py           ← entire application (294 lines)
│   ├── process_etoro_statement(file_path)  ← reads Account Summary + Financial Summary sheets
│   ├── calculate_roi(metrics)              ← net realized profit / net investment
│   ├── format_financial_table(metrics)     ← Rich table (4 sections, green/red coloring)
│   └── main()                             ← CLI entry, prints table, saves CSV
└── tests/
    └── test_etoro_summary.py              ← 5 test classes, ~15 tests (no Excel I/O mocking)
```

## Key Behaviors

- Reads two sheets from the eToro Excel: `Account Summary` and `Financial Summary`
- Extracts: deposits, withdrawals, realized gains, dividends, fees, equity
- Handles 4 column-name variants for the amount column (eToro changes these between exports)
- Rich table sections: Investment / Realized / Unrealized / Performance
- Positive values colored green, negative red
- Exits with `SystemExit` on missing file

## CI

- `ci.yml`: ruff check + format → pytest with hashed lockfile (Python 3.12, push/PR to master)
- `sonarcloud.yml`: pytest --cov → SonarCloud scan
- `deps-refresh.yml`: monthly pip-compile --upgrade --generate-hashes → auto PR (6th of month)
- `dependabot-auto-merge.yml`: auto-squash patch/minor; major = manual review

## Key Conventions

- Line length: 100 chars (ruff)
- mypy: strict mode on the module
- `tabulate` is in `requirements.txt` but unused — do not add usage without removing this note
- A real eToro statement xlsx (2023–2026) is committed as test fixture; do not delete it
- Branch: `master`
