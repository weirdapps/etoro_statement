"""Tests for etoro_summary.py."""

import pandas as pd
import pytest

from etoro_summary import (
    CURRENT_REALIZED_EQUITY,
    CURRENT_UNREALIZED_EQUITY,
    DIVIDEND_INCOME,
    NET_INVESTMENT,
    NET_REALIZED_PROFIT,
    OTHER_INCOME,
    REALIZED_GAINS,
    RETURN_ON_INVESTMENT,
    TOTAL_DEPOSITS,
    TOTAL_EXPENSES_AND_FEES,
    TOTAL_WITHDRAWALS,
    UNREALIZED_PROFIT,
    calculate_roi,
    format_financial_table,
    process_etoro_statement,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_metrics():
    """Return a zeroed-out metrics dict matching process_etoro_statement output."""
    return {
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


def _write_statement(path, account_rows, financial_rows):
    """Write a synthetic two-sheet eToro statement to ``path``. Fabricated figures only."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(account_rows, columns=["Details", "Amount"]).to_excel(
            writer, sheet_name="Account Summary", index=False
        )
        pd.DataFrame(financial_rows, columns=["Name", "Amount in (USD)"]).to_excel(
            writer, sheet_name="Financial Summary", index=False
        )
    return path


# ---------------------------------------------------------------------------
# 1. Import / module-level constants
# ---------------------------------------------------------------------------


class TestImports:
    """Verify that the module and its public API are importable."""

    def test_module_imports(self):
        import etoro_summary  # noqa: F811

        assert etoro_summary is not None

    def test_key_constants_exist(self):
        assert TOTAL_DEPOSITS == "Total Deposits"
        assert RETURN_ON_INVESTMENT == "Return on Investment"

    def test_public_functions_exist(self):
        assert callable(process_etoro_statement)
        assert callable(format_financial_table)
        assert callable(calculate_roi)


# ---------------------------------------------------------------------------
# 2. calculate_roi
# ---------------------------------------------------------------------------


class TestCalculateRoi:
    """Unit tests for the ROI calculation helper."""

    def test_positive_roi(self):
        metrics = _empty_metrics()
        metrics[NET_INVESTMENT] = 10000.0
        metrics[NET_REALIZED_PROFIT] = 2500.0
        roi_value, roi_str = calculate_roi(metrics)
        assert roi_value == pytest.approx(25.0)
        assert roi_str == "+25.00%"

    def test_negative_roi(self):
        metrics = _empty_metrics()
        metrics[NET_INVESTMENT] = 10000.0
        metrics[NET_REALIZED_PROFIT] = -1500.0
        roi_value, roi_str = calculate_roi(metrics)
        assert roi_value == pytest.approx(-15.0)
        assert roi_str == "-15.00%"

    def test_zero_investment_returns_na(self):
        metrics = _empty_metrics()
        metrics[NET_INVESTMENT] = 0.0
        metrics[NET_REALIZED_PROFIT] = 500.0
        roi_value, roi_str = calculate_roi(metrics)
        assert roi_value == 0
        assert roi_str == "N/A"

    def test_zero_profit_returns_zero_pct(self):
        metrics = _empty_metrics()
        metrics[NET_INVESTMENT] = 5000.0
        metrics[NET_REALIZED_PROFIT] = 0.0
        roi_value, roi_str = calculate_roi(metrics)
        assert roi_value == pytest.approx(0.0)
        assert roi_str == "0.00%"


# ---------------------------------------------------------------------------
# 3. Metrics dict structure
# ---------------------------------------------------------------------------


class TestMetricsStructure:
    """Validate the shape of the metrics dictionary."""

    def test_empty_metrics_has_all_keys(self):
        m = _empty_metrics()
        expected_keys = {
            TOTAL_DEPOSITS,
            TOTAL_WITHDRAWALS,
            NET_INVESTMENT,
            REALIZED_GAINS,
            DIVIDEND_INCOME,
            OTHER_INCOME,
            TOTAL_EXPENSES_AND_FEES,
            NET_REALIZED_PROFIT,
            CURRENT_REALIZED_EQUITY,
            CURRENT_UNREALIZED_EQUITY,
            UNREALIZED_PROFIT,
        }
        assert set(m.keys()) == expected_keys

    def test_all_values_start_at_zero(self):
        m = _empty_metrics()
        for v in m.values():
            assert v == 0.0


# ---------------------------------------------------------------------------
# 4. format_financial_table smoke test
# ---------------------------------------------------------------------------


class TestFormatFinancialTable:
    """Verify table formatting doesn't crash on valid input."""

    def test_returns_rich_table(self):
        from rich.table import Table

        metrics = _empty_metrics()
        metrics[NET_INVESTMENT] = 10000.0
        metrics[NET_REALIZED_PROFIT] = 1000.0
        table = format_financial_table(metrics)
        assert isinstance(table, Table)


# ---------------------------------------------------------------------------
# 5. process_etoro_statement error handling
# ---------------------------------------------------------------------------


class TestProcessStatementErrors:
    """Ensure process_etoro_statement fails gracefully on bad input."""

    def test_missing_file_exits(self):
        with pytest.raises(SystemExit):
            process_etoro_statement("/nonexistent/file.xlsx")


# ---------------------------------------------------------------------------
# 6. process_etoro_statement categorisation
# ---------------------------------------------------------------------------


class TestProcessStatementCategorisation:
    """Run process_etoro_statement on a synthetic statement and check the buckets."""

    def test_negative_profit_or_loss_nets_against_realized_gains(self, tmp_path):
        # Regression: a negative "Profit or Loss" row matched no branch and was
        # dropped, so this statement reported Realized Gains 500, Net Realized
        # Profit 520 and ROI +5.20% instead of 200, 220 and +2.20%.
        statement = _write_statement(
            tmp_path / "statement.xlsx",
            account_rows=[("Deposits", 10000.0)],
            financial_rows=[
                ("Stocks (Profit or Loss)", 500.0),
                ("CFDs (Profit or Loss)", -300.0),
                ("Dividends", 20.0),
            ],
        )

        metrics = process_etoro_statement(statement)

        assert metrics[REALIZED_GAINS] == pytest.approx(200.0)
        assert metrics[DIVIDEND_INCOME] == pytest.approx(20.0)
        assert metrics[TOTAL_EXPENSES_AND_FEES] == pytest.approx(0.0)
        assert metrics[NET_REALIZED_PROFIT] == pytest.approx(220.0)
        assert calculate_roi(metrics)[1] == "+2.20%"
