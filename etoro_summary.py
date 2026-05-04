#!/usr/bin/env python3
"""
eToro Financial Summary Generator

This script processes an eToro account statement Excel file and generates
a comprehensive financial summary table.

Usage:
    python etoro_summary.py path_to_statement.xlsx

Requirements:
    - pandas
    - openpyxl
    - rich
"""

import sys

import pandas as pd
from rich import box
from rich.console import Console
from rich.table import Table

# Financial metrics constants
TOTAL_DEPOSITS = "Total Deposits"
TOTAL_WITHDRAWALS = "Total Withdrawals"
NET_INVESTMENT = "Net Investment"
REALIZED_GAINS = "Realized Gains"
DIVIDEND_INCOME = "Dividend Income"
OTHER_INCOME = "Other Income"
TOTAL_EXPENSES_AND_FEES = "Total Expenses and Fees"
NET_REALIZED_PROFIT = "Net Realized Profit"
CURRENT_REALIZED_EQUITY = "Current Realized Equity"
CURRENT_UNREALIZED_EQUITY = "Current Unrealized Equity"
UNREALIZED_PROFIT = "Unrealized Profit"
RETURN_ON_INVESTMENT = "Return on Investment"
PROFIT_OR_LOSS = "Profit or Loss"


def process_etoro_statement(file_path):  # noqa: S3776 - sequential data extraction orchestration
    """Process eToro statement Excel file and return key financial metrics."""

    # Load all sheets from the Excel file
    try:
        account_summary = pd.read_excel(file_path, sheet_name="Account Summary")
        financial_summary = pd.read_excel(file_path, sheet_name="Financial Summary")
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)

    # Initialize metrics dictionary
    metrics = {
        TOTAL_DEPOSITS: 0.0,
        TOTAL_WITHDRAWALS: 0.0,
        NET_INVESTMENT: 0.0,
        REALIZED_GAINS: 0.0,
        DIVIDEND_INCOME: 0.0,
        OTHER_INCOME: 0.0,
        TOTAL_EXPENSES_AND_FEES: 0.0,
        NET_REALIZED_PROFIT: 0.0,
        CURRENT_REALIZED_EQUITY: 0.0,
        CURRENT_UNREALIZED_EQUITY: 0.0,
        UNREALIZED_PROFIT: 0.0,
    }

    # 1. Extract deposits and withdrawals from Account Summary
    for _, row in account_summary.iterrows():
        if pd.notna(row.get("Details")):
            details = row["Details"]

            if details == "Deposits" and pd.notna(row.iloc[1]):
                metrics[TOTAL_DEPOSITS] = float(row.iloc[1])
            elif details == "Withdrawals" and pd.notna(row.iloc[1]):
                metrics[TOTAL_WITHDRAWALS] = float(row.iloc[1])
            elif details == "Ending Realized Equity" and pd.notna(row.iloc[1]):
                metrics[CURRENT_REALIZED_EQUITY] = float(row.iloc[1])
            elif details == "Ending Unrealized Equity" and pd.notna(row.iloc[1]):
                metrics[CURRENT_UNREALIZED_EQUITY] = float(row.iloc[1])

    # 2. Calculate Net Investment
    metrics[NET_INVESTMENT] = metrics[TOTAL_DEPOSITS] - abs(metrics[TOTAL_WITHDRAWALS])

    # 3. Extract realized gains, dividends, other income, and expenses from Financial Summary
    amount_columns = [
        "Amount\r\n in (USD)",
        "Amount in (USD)",
        "Amount\nin (USD)",
        "Amount (USD)",
    ]

    amount_column = None
    for col in amount_columns:
        if col in financial_summary.columns:
            amount_column = col
            break

    if not amount_column:
        for col in financial_summary.columns:
            if "Amount" in str(col) and "USD" in str(col):
                amount_column = col
                break

    if not amount_column:
        print("ERROR: Could not find amount column in Financial Summary sheet")
        return metrics

    # Process financial summary with the correct column name
    for _, row in financial_summary.iterrows():
        if pd.notna(row.get("Name")) and pd.notna(row.get(amount_column)):
            name = row["Name"]
            amount = 0.0

            try:
                amount = float(row[amount_column])
            except (ValueError, TypeError):
                continue

            # Categorize financial items
            if PROFIT_OR_LOSS in name and amount > 0:
                metrics[REALIZED_GAINS] += amount
            elif "Dividend" in name:
                metrics[DIVIDEND_INCOME] += amount
            elif (
                "fee" in name.lower()
                or "charge" in name.lower()
                or (amount < 0 and "Dividend" not in name and PROFIT_OR_LOSS not in name)
            ):
                # Store expenses as positive values for consistent handling
                metrics[TOTAL_EXPENSES_AND_FEES] += abs(amount)
            elif amount > 0 and PROFIT_OR_LOSS not in name and "Dividend" not in name:
                metrics[OTHER_INCOME] += amount

    # 4. Calculate Net Realized Profit
    metrics[NET_REALIZED_PROFIT] = (
        metrics[REALIZED_GAINS]
        + metrics[DIVIDEND_INCOME]
        + metrics[OTHER_INCOME]
        - metrics[TOTAL_EXPENSES_AND_FEES]  # Expenses should be subtracted from profit
    )

    # 5. Calculate Unrealized Profit
    if metrics[CURRENT_UNREALIZED_EQUITY] > 0 and metrics[CURRENT_REALIZED_EQUITY] > 0:
        metrics[UNREALIZED_PROFIT] = (
            metrics[CURRENT_UNREALIZED_EQUITY] - metrics[CURRENT_REALIZED_EQUITY]
        )

    return metrics


def format_financial_table(metrics):  # noqa: S3776 - presentation formatting logic
    """Format the metrics into a clean, minimal tabular presentation using Rich."""

    # Calculate ROI
    roi_value, roi_formatted = calculate_roi(metrics)
    metrics[RETURN_ON_INVESTMENT] = roi_formatted

    # Create a structured Rich table with better styling
    table = Table(
        title="eToro Financial Summary",
        title_justify="left",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold",
        padding=(0, 2),
        expand=False,
    )
    table.add_column("METRIC", no_wrap=True)
    table.add_column("VALUE", justify="right")

    # Define the table structure with sections
    table_structure = [
        # Section: Investment Summary
        {
            "section": "Investment",
            "metrics": [TOTAL_DEPOSITS, TOTAL_WITHDRAWALS, NET_INVESTMENT],
        },
        # Section: Realized Performance
        {
            "section": "Realized",
            "metrics": [
                REALIZED_GAINS,
                DIVIDEND_INCOME,
                OTHER_INCOME,
                TOTAL_EXPENSES_AND_FEES,
                NET_REALIZED_PROFIT,
                CURRENT_REALIZED_EQUITY,
            ],
        },
        # Section: Unrealized Performance
        {
            "section": "Unrealized",
            "metrics": [UNREALIZED_PROFIT, CURRENT_UNREALIZED_EQUITY],
        },
        # Section: Performance Metrics
        {"section": "Performance", "metrics": [RETURN_ON_INVESTMENT]},
    ]

    # Populate the table with sections and metrics
    for i, section in enumerate(table_structure):
        # Add section header with horizontal line above (except for first section)
        if i > 0:
            table.add_row("", "", end_section=True)
        table.add_row(f"[bold]{section['section']}[/bold]", "")

        # Add metrics for this section
        for key in section["metrics"]:
            if key in metrics:
                value = metrics[key]
                if pd.notna(value) and (value != 0 or key == "Return on Investment"):
                    # Format value appropriately
                    if isinstance(value, str):
                        formatted_value = value
                    else:
                        # Special case for expenses and fees - show as negative
                        if key == TOTAL_EXPENSES_AND_FEES:
                            value = -abs(value)  # Make expenses negative
                            formatted_value = f"-${abs(value):,.2f}"
                        else:
                            formatted_value = f"${abs(value):,.2f}"

                            # Add plus/minus sign for all monetary values
                            if value > 0:
                                formatted_value = f"+{formatted_value}"
                            elif value < 0:
                                formatted_value = f"-{formatted_value}"

                    # Determine color based on value (using minimal color palette)
                    value_style = ""
                    if isinstance(value, str):
                        if RETURN_ON_INVESTMENT in key and "N/A" not in value:
                            roi_numeric = float(value.replace("%", "").replace("+", ""))
                            value_style = "green" if roi_numeric > 0 else "red"
                    else:
                        # Color all positive values green and negatives red
                        if value > 0:
                            value_style = "green"
                        elif value < 0:
                            value_style = "red"
                        # Special case for withdrawals which are negative values but not losses
                        if "Withdrawals" in key:
                            value_style = ""

                    # Simplify key names by removing "Total" and truncating
                    display_key = key.replace("Total ", "")

                    # Add row with appropriate styling
                    if value_style:
                        table.add_row(f"  {display_key}", f"[{value_style}]{formatted_value}[/]")
                    else:
                        table.add_row(f"  {display_key}", formatted_value)
                else:
                    table.add_row(f"  {key}", "N/A", style="dim")

    return table


def calculate_roi(metrics):
    """Calculate and return the ROI as a percentage and value."""
    if metrics[NET_INVESTMENT] != 0:
        roi = (metrics[NET_REALIZED_PROFIT] / abs(metrics[NET_INVESTMENT])) * 100
        sign = "+" if roi > 0 else ""
        return roi, f"{sign}{roi:.2f}%"
    return 0, "N/A"


def main():
    """Main function to process file and output results."""

    # Initialize Rich console
    console = Console()

    # Check for input file argument
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/] python etoro_summary.py <path_to_etoro_statement.xlsx>")
        sys.exit(1)

    file_path = sys.argv[1]
    metrics = process_etoro_statement(file_path)

    # Print the formatted table using Rich
    table = format_financial_table(metrics)
    console.print(table)

    # ROI is now in the table, no need to print separately

    # Save the metrics to a CSV file
    metrics_df = pd.DataFrame(list(metrics.items()), columns=["Metric", "Value"])
    csv_path = file_path.replace(".xlsx", "_summary.csv")
    metrics_df.to_csv(csv_path, index=False)


if __name__ == "__main__":
    main()
