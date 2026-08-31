from pathlib import Path
from typing import Optional

import pandas as pd

from backend.financial.schema import FinancialMetric


class ScreenerParser:
    """
    Parser for Screener.in Excel exports.

    Supported sheets:
        - BS
        - P&L
        - Cashflows

    V1 extracts historical financial-year data only.
    """

    EXPECTED_SHEETS = ("BS", "P&L", "Cashflows")

    SOURCE_NAME = "Screener"

    # Screener label -> canonical metric name
    FIELD_MAP = {
        # Balance Sheet
        "Borrowings": "borrowings",
        "Working Capital": "working_capital",
        "Debtors": "accounts_receivable",
        "Inventory": "inventory",

        # Income Statement
        "Sales": "revenue",
        "Expenses": "operating_expenses",
        "Operating Profit": "operating_profit",
        "Other Income": "other_income",
        "Depreciation": "depreciation",
        "Interest": "finance_cost",
        "Profit before tax": "profit_before_tax",
        "Tax": "tax",
        "Net profit": "net_profit",
        "EPS": "eps",
        "Price to earning": "price_to_earnings",
        "Price": "share_price",
        "OPM": "operating_profit_margin",

        # Cash Flow
        "Cash from Operating Activity": "operating_cash_flow",
        "Cash from Investing Activity": "investing_cash_flow",
        "Cash from Financing Activity": "financing_cash_flow",
        "Net Cash Flow": "net_cash_flow",
    }

    # Canonical metric -> unit
    UNIT_MAP = {
        # Monetary values
        "revenue": "crore",
        "operating_expenses": "crore",
        "operating_profit": "crore",
        "other_income": "crore",
        "depreciation": "crore",
        "finance_cost": "crore",
        "profit_before_tax": "crore",
        "tax": "crore",
        "net_profit": "crore",
        "borrowings": "crore",
        "working_capital": "crore",
        "accounts_receivable": "crore",
        "inventory": "crore",
        "operating_cash_flow": "crore",
        "investing_cash_flow": "crore",
        "financing_cash_flow": "crore",
        "net_cash_flow": "crore",

        # Non-monetary values
        "eps": "INR_per_share",
        "share_price": "INR_per_share",
        "price_to_earnings": "multiple",
        "operating_profit_margin": "ratio",
    }

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Screener file not found: {self.file_path}"
            )

        if self.file_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError(
                "Screener input must be an Excel file (.xlsx or .xls)."
            )

        self.workbook = pd.ExcelFile(self.file_path)

    # =========================================================
    # Workbook handling
    # =========================================================

    def get_sheets(self) -> list[str]:
        """Return all worksheet names."""

        return self.workbook.sheet_names

    def validate_workbook(self) -> None:
        """Validate that all required Screener sheets exist."""

        actual_sheets = set(self.get_sheets())
        missing = set(self.EXPECTED_SHEETS) - actual_sheets

        if missing:
            raise ValueError(
                "Invalid Screener workbook. "
                f"Missing sheets: {sorted(missing)}"
            )

    def read_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Read a Screener worksheet without assuming headers."""

        if sheet_name not in self.get_sheets():
            raise ValueError(
                f"Sheet '{sheet_name}' does not exist. "
                f"Available sheets: {self.get_sheets()}"
            )

        return pd.read_excel(
            self.file_path,
            sheet_name=sheet_name,
            header=None,
        )

    def load(self) -> dict[str, pd.DataFrame]:
        """Load all expected Screener sheets."""

        self.validate_workbook()

        return {
            sheet: self.read_sheet(sheet)
            for sheet in self.EXPECTED_SHEETS
        }

    # =========================================================
    # Company information
    # =========================================================

    def get_company_name(self) -> Optional[str]:
        """Extract company name from the first cell."""

        first_sheet = self.get_sheets()[0]
        df = self.read_sheet(first_sheet)

        if df.empty:
            return None

        value = df.iloc[0, 0]

        if pd.isna(value):
            return None

        return str(value).strip()

    # =========================================================
    # Period handling
    # =========================================================

    @staticmethod
    def is_historical_period(value) -> bool:
        """
        Return True only for actual date-based financial periods.

        This deliberately excludes:
            Trailing
            Best Case
            Worst Case
        """

        if pd.isna(value):
            return False

        if isinstance(value, pd.Timestamp):
            return True

        if hasattr(value, "year"):
            return True

        return False

    @staticmethod
    def format_period(value) -> Optional[str]:
        """Convert a date into FYYYYY format."""

        if pd.isna(value):
            return None

        if isinstance(value, pd.Timestamp):
            return f"FY{value.year}"

        if hasattr(value, "year"):
            return f"FY{value.year}"

        return str(value).strip()

    # =========================================================
    # Value handling
    # =========================================================

    @staticmethod
    def clean_value(value) -> Optional[float]:
        """Convert a Screener cell to a numeric value."""

        if pd.isna(value):
            return None

        if isinstance(value, str):
            value = value.strip()

            if value in {"", "-", "--", "—"}:
                return None

            value = value.replace(",", "")

            try:
                return float(value)
            except ValueError:
                return None

        if isinstance(value, (int, float)):
            return float(value)

        return None

    # =========================================================
    # Metric extraction
    # =========================================================

    def extract_sheet_metrics(
        self,
        sheet_name: str,
    ) -> list[FinancialMetric]:
        """
        Extract supported historical metrics from one sheet.
        """

        df = self.read_sheet(sheet_name)

        if len(df) < 4:
            return []

        # In the observed Screener export:
        # row 0 -> company
        # row 1 -> blank
        # row 2 -> headers
        # row 3 onward -> data
        header_row = df.iloc[2]

        metrics: list[FinancialMetric] = []

        for row_idx in range(3, len(df)):

            metric_label = df.iloc[row_idx, 0]

            if pd.isna(metric_label):
                continue

            metric_label = str(metric_label).strip()

            if metric_label not in self.FIELD_MAP:
                continue

            canonical_name = self.FIELD_MAP[metric_label]

            unit = self.UNIT_MAP.get(canonical_name)

            for column_idx in range(1, len(df.columns)):

                period_value = header_row.iloc[column_idx]

                if not self.is_historical_period(period_value):
                    continue

                period = self.format_period(period_value)

                value = self.clean_value(
                    df.iloc[row_idx, column_idx]
                )

                metrics.append(
                    FinancialMetric(
                        name=canonical_name,
                        value=value,
                        period=period,
                        currency="INR",
                        unit=unit,
                        source=self.SOURCE_NAME,
                        source_field=metric_label,
                        source_sheet=sheet_name,
                        source_row=row_idx + 1,
                    )
                )

        return metrics

    # =========================================================
    # Full extraction
    # =========================================================

    def extract_metrics(self) -> list[FinancialMetric]:
        """Extract all supported historical metrics."""

        self.validate_workbook()

        metrics: list[FinancialMetric] = []

        for sheet in self.EXPECTED_SHEETS:
            metrics.extend(
                self.extract_sheet_metrics(sheet)
            )

        return metrics

    # =========================================================
    # Inspection
    # =========================================================

    def inspect_sheet(self, sheet_name: str) -> dict:
        """Return structural information about one sheet."""

        df = self.read_sheet(sheet_name)

        return {
            "sheet": sheet_name,
            "rows": len(df),
            "columns": len(df.columns),
            "first_rows": (
                df.head(20)
                .fillna("")
                .values
                .tolist()
            ),
        }

    def inspect(self) -> dict:
        """Inspect the Screener workbook structure."""

        self.validate_workbook()

        result = {
            "file": str(self.file_path),
            "company": self.get_company_name(),
            "sheets": self.get_sheets(),
            "sheet_details": {},
        }

        for sheet in self.get_sheets():
            result["sheet_details"][sheet] = (
                self.inspect_sheet(sheet)
            )

        return result