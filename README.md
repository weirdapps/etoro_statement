# eToro Account Statement Processor

[![CI](https://github.com/weirdapps/etoro_statement/actions/workflows/ci.yml/badge.svg)](https://github.com/weirdapps/etoro_statement/actions/workflows/ci.yml)
[![CodeQL](https://github.com/weirdapps/etoro_statement/actions/workflows/codeql.yml/badge.svg)](https://github.com/weirdapps/etoro_statement/actions/workflows/codeql.yml)
[![SonarCloud](https://github.com/weirdapps/etoro_statement/actions/workflows/sonarcloud.yml/badge.svg)](https://github.com/weirdapps/etoro_statement/actions/workflows/sonarcloud.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

A Python tool that processes eToro account statements and generates comprehensive financial summaries.

## Overview

Extracts key financial metrics from eToro Excel-based account statements and presents them in a clean, organized table. Results are also saved to CSV for further analysis.

**Metrics covered:**

- **Investment summary** — deposits, withdrawals, net investment
- **Realized performance** — gains, dividends, other income, expenses and fees, net realized profit
- **Unrealized performance** — unrealized profit, current equity
- **ROI** — return on investment as a percentage of net realized profit over net investment (excludes timing of cash flows and unrealized gains)

## Requirements

- Python 3.12
- `pandas`
- `openpyxl`
- `rich`

Install dependencies:

```bash
pip install pandas openpyxl rich
```

## Usage

```bash
python etoro_summary.py path_to_statement.xlsx
```

### Example

```bash
python etoro_summary.py etoro-account-statement-1-1-2023-5-15-2025.xlsx
```

The tool will:

1. Read the `Account Summary` and `Financial Summary` sheets from the Excel file
2. Display a formatted financial summary in the terminal
3. Save a CSV file with the complete metrics alongside the input file

## Output

![Example output showing a formatted financial summary table](example_output.png)

## License

[MIT](LICENSE)
