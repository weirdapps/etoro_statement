# eToro Account Statement Processor

A Python tool that processes eToro account statements and generates comprehensive financial summaries.

## Overview

This tool extracts essential financial metrics from eToro Excel-based account statements and provides a clean, organized summary focusing on:

- Investment summary (deposits, withdrawals, net investment)
- Realized performance (gains, dividends, income, expenses, profits)
- Unrealized performance (unrealized profit, current equity)
- Performance metrics (Return on Investment)

The tool automatically saves all extracted metrics to a CSV file for further analysis.

## Requirements

- Python 3.6+
- pandas
- openpyxl
- rich
- tabulate

Install the required packages with:

```bash
pip install pandas openpyxl rich tabulate
```

## Usage

```bash
python etoro_summary.py path_to_statement.xlsx
```

### Example

```bash
python etoro_summary.py etoro-account-statement-1-1-2023-5-15-2025.xlsx
```

This will:
1. Process the eToro statement file
2. Display a comprehensive financial summary in the terminal
3. Generate a CSV file with the complete metrics (saved in the same directory as the input file)

## Output Example

The tool generates a clean, minimal formatted table with sections:

```
 eToro Financial Summary 
 METRIC                             VALUE 
 Investment                      
   Deposits                   $390,933.67 
   Withdrawals                $22,500.00 
   Net Investment             $368,433.67 
 ────────────────────────────────
 Realized                        
   Realized Gains             +$28,726.33 
   Dividend Income             +$1,417.25 
   Other Income                +$4,473.93 
   Expenses and Fees           -$1,090.28 
   Net Realized Profit        +$33,527.23 
   Current Realized Equity    $402,850.35 
 ────────────────────────────────
 Unrealized                      
   Unrealized Profit          +$24,080.08 
   Current Unrealized Equity  $426,930.43 
 ────────────────────────────────
 Performance                     
   Return on Investment            9.10% 
```

ROI is calculated and displayed as a percentage based on Net Realized Profit divided by the absolute value of Net Investment.

