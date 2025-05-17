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

import pandas as pd
import sys
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich import box

def process_etoro_statement(file_path):
    """Process eToro statement Excel file and return key financial metrics."""
    
    # Load all sheets from the Excel file
    try:
        account_summary = pd.read_excel(file_path, sheet_name='Account Summary')
        financial_summary = pd.read_excel(file_path, sheet_name='Financial Summary')
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)
    
    # Initialize metrics dictionary
    metrics = {
        'Total Deposits': 0,
        'Total Withdrawals': 0,
        'Net Investment': 0,
        'Realized Gains': 0,
        'Dividend Income': 0,
        'Other Income': 0,
        'Total Expenses and Fees': 0,
        'Net Realized Profit': 0,
        'Current Realized Equity': 0,
        'Current Unrealized Equity': 0,
        'Unrealized Profit': 0
    }
    
    # 1. Extract deposits and withdrawals from Account Summary
    for _, row in account_summary.iterrows():
        if pd.notna(row.get('Details')):
            details = row['Details']
            
            if details == 'Deposits' and pd.notna(row.iloc[1]):
                metrics['Total Deposits'] = float(row.iloc[1])
            elif details == 'Withdrawals' and pd.notna(row.iloc[1]):
                metrics['Total Withdrawals'] = float(row.iloc[1])
            elif details == 'Ending Realized Equity' and pd.notna(row.iloc[1]):
                metrics['Current Realized Equity'] = float(row.iloc[1])
            elif details == 'Ending Unrealized Equity' and pd.notna(row.iloc[1]):
                metrics['Current Unrealized Equity'] = float(row.iloc[1])
    
    # 2. Calculate Net Investment
    metrics['Net Investment'] = metrics['Total Deposits'] - abs(metrics['Total Withdrawals'])
    
    # 3. Extract realized gains, dividends, other income, and expenses from Financial Summary
    amount_columns = [
        'Amount\r\n in (USD)',
        'Amount in (USD)',
        'Amount\nin (USD)',
        'Amount (USD)'
    ]
    
    amount_column = None
    for col in amount_columns:
        if col in financial_summary.columns:
            amount_column = col
            break
    
    if not amount_column:
        for col in financial_summary.columns:
            if 'Amount' in str(col) and 'USD' in str(col):
                amount_column = col
                break
    
    if not amount_column:
        print("ERROR: Could not find amount column in Financial Summary sheet")
        return metrics
    
    # Process financial summary with the correct column name
    for _, row in financial_summary.iterrows():
        if pd.notna(row.get('Name')) and pd.notna(row.get(amount_column)):
            name = row['Name']
            amount = 0
            
            try:
                amount = float(row[amount_column])
            except (ValueError, TypeError):
                continue
            
            
            # Categorize financial items
            if "Profit or Loss" in name and amount > 0:
                metrics['Realized Gains'] += amount
            elif "Dividend" in name:
                metrics['Dividend Income'] += amount
            elif "fee" in name.lower() or "charge" in name.lower() or (amount < 0 and not "Dividend" in name and not "Profit or Loss" in name):
                metrics['Total Expenses and Fees'] += abs(amount)
            elif amount > 0 and not "Profit or Loss" in name and not "Dividend" in name:
                metrics['Other Income'] += amount
    
    # 4. Calculate Net Realized Profit
    metrics['Net Realized Profit'] = (
        metrics['Realized Gains'] + 
        metrics['Dividend Income'] + 
        metrics['Other Income'] + 
        metrics['Total Expenses and Fees']  # Expenses are now negative, so we add them
    )
    
    # 5. Calculate Unrealized Profit
    if metrics['Current Unrealized Equity'] > 0 and metrics['Current Realized Equity'] > 0:
        metrics['Unrealized Profit'] = metrics['Current Unrealized Equity'] - metrics['Current Realized Equity']
    
    return metrics


def format_financial_table(metrics):
    """Format the metrics into a clean, minimal tabular presentation using Rich."""
    
    # Calculate ROI
    roi_value, roi_formatted = calculate_roi(metrics)
    metrics['Return on Investment'] = roi_formatted
    
    # Create a structured Rich table with better styling
    table = Table(
        title="eToro Financial Summary", 
        title_justify="left",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold",
        padding=(0, 2),
        expand=False
    )
    table.add_column("METRIC", no_wrap=True)
    table.add_column("VALUE", justify="right")
    
    # Define the table structure with sections
    table_structure = [
        # Section: Investment Summary
        {"section": "Investment", "metrics": [
            "Total Deposits",
            "Total Withdrawals",
            "Net Investment"
        ]},
        # Section: Realized Performance
        {"section": "Realized", "metrics": [
            "Realized Gains",
            "Dividend Income",
            "Other Income",
            "Total Expenses and Fees",
            "Net Realized Profit",
            "Current Realized Equity"
        ]},
        # Section: Unrealized Performance
        {"section": "Unrealized", "metrics": [
            "Unrealized Profit",
            "Current Unrealized Equity"
        ]},
        # Section: Performance Metrics
        {"section": "Performance", "metrics": [
            "Return on Investment"
        ]}
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
                if pd.notna(value) and (value != 0 or key == 'Return on Investment'):
                    # Format value appropriately
                    if isinstance(value, str):
                        formatted_value = value
                    else:
                        # Special case for expenses and fees - show as negative
                        if key == 'Total Expenses and Fees':
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
                        if "Return on Investment" in key and "N/A" not in value:
                            roi_numeric = float(value.replace('%', '').replace('+', ''))
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
    if metrics['Net Investment'] != 0:
        roi = (metrics['Net Realized Profit'] / abs(metrics['Net Investment'])) * 100
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
    metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
    csv_path = file_path.replace('.xlsx', '_summary.csv')
    metrics_df.to_csv(csv_path, index=False)


if __name__ == "__main__":
    main()