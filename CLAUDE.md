# etoro_statement

Single-script tool that reads an eToro Excel account statement and outputs a formatted financial summary to the terminal, then saves a CSV alongside the input file.

## Tech Stack

- Python 3.11+ (mypy/ruff target), CI runs 3.12 (SonarCloud job runs 3.11)
- pandas, openpyxl, rich, tabulate
- Managed by `uv`. `pyproject.toml` declares `[project]` deps plus tool config (ruff, mypy, pytest);
  `[tool.uv] package = false`, so the project itself is never built or installed, only its deps
- Lockfile: `uv.lock`. Migrated off pip-compile / `requirements-lock.txt` in commit 20a52b8

## Running

```bash
uv sync --frozen
uv run python etoro_summary.py <path-to-statement.xlsx>
# outputs formatted Rich table to terminal
# saves <input>_summary.csv alongside the xlsx
```

## Testing

```bash
uv sync --frozen
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

## Code Organization

Flat single-script layout, no package structure:

```text
etoro_statement/
├── etoro_summary.py           ← entire application (293 lines)
│   ├── process_etoro_statement(file_path)  ← reads Account Summary + Financial Summary sheets
│   ├── calculate_roi(metrics)              ← net realized profit / net investment
│   ├── format_financial_table(metrics)     ← Rich table (4 sections, green/red coloring)
│   └── main()                             ← CLI entry, prints table, saves CSV
└── tests/
    └── test_etoro_summary.py              ← 5 test classes, 11 tests (no Excel I/O mocking)
```

## Key Behaviors

- Reads two sheets from the eToro Excel: `Account Summary` and `Financial Summary`
- Extracts: deposits, withdrawals, realized gains, dividends, fees, equity
- Handles 4 column-name variants for the amount column (eToro changes these between exports)
- Rich table sections: Investment / Realized / Unrealized / Performance
- Positive values colored green, negative red
- Exits with `SystemExit` on missing file
- If NO amount column matches, it prints an ERROR line, then still exits 0 and still writes the CSV
  with every Financial Summary metric at zero. Silent-zero output, not a crash

This script makes no network calls, so there is no eToro API surface here. Do not add one without
being asked.

## CI

- `ci.yml`: `uv sync --frozen` → ruff check + ruff format --check → pytest (Python 3.12, push/PR to master)
- `codeql.yml`: CodeQL python analysis (push/PR + Mondays 06:00 UTC)
- `sonarcloud.yml`: `uv sync --frozen` → pytest --cov → SonarCloud scan (skipped if `SONAR_TOKEN` unset)
- `deps-refresh.yml`: monthly `uv lock --upgrade` → validate (ruff check + ruff format --check +
  pytest, deliberately mirrors `ci.yml`) → auto PR (6th, 04:23 UTC) → republish the validate verdict
  as a `deps-refresh / validate` commit status on the new PR head
- `dependabot-auto-merge.yml`: thin caller, delegates to
  `weirdapps/shared-workflows/.github/workflows/dependabot-auto-merge.yml@main`. No inputs passed, so
  defaults apply: patch/minor auto-merge, standalone major stays manual, grouped major auto-merges.
  Do not reintroduce a local implementation

### Why a deps-refresh PR carries only one check

`PUSH_PAT` is not set on this repo, so `deps-refresh.yml` falls back to `github.token` and the PR is
opened by `github-actions[bot]`. GitHub parks every workflow run whose triggering actor is that
identity at `conclusion: action_required` with **zero check runs**, which is why such a PR reads as
"no checks reported" rather than as failing. Verified 2026-08-11 on PR #45 and again on PR #49.

Two things that look like the cause but are not, both falsified by experiment:

- The `fork-pr-contributor-approval` policy (`first_time_contributors`). PR #45's merge promoted
  `github-actions[bot]` to `author_association: CONTRIBUTOR`, yet the very next refresh PR (#49) was
  still parked. The gate keys on the triggering actor, not on contributor status.
- Branch protection. `master` has only `deletion` and `non_fast_forward` rules and no required
  status checks.

So `deps-refresh.yml` republishes its own validate verdict as a `deps-refresh / validate` commit
status on the new head. To also get the native CI, CodeQL and SonarCloud results, release the parked
runs with `gh api --method POST repos/weirdapps/etoro_statement/actions/runs/<id>/approve`. The real
fix is a `PUSH_PAT` repo secret (PAT or GitHub App token) so the PR is not bot-authored. Do not
loosen the approval policy to work around this.

## Key Conventions

- Line length: 100 chars (ruff), though `E501` is in the ignore list
- mypy is NOT strict: `disallow_untyped_defs = false`, `ignore_missing_imports = true`. It is also
  not a dev dependency and no CI job runs it; it only runs via the pre-commit hook
- `tabulate` is a declared runtime dep in `pyproject.toml` but is never imported. Do not add usage
  without removing this note
- PUBLIC repo. `.gitignore` excludes `*.xlsx`, `*.xls`, `*.csv`. A real eToro statement sits
  untracked in the working tree as a local fixture: never `git add` it, and never `git add -A`.
  It has never been committed and must stay that way
- Branch: `master`
