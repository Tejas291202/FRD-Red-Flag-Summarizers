from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class FinancialMetric:
    """
    Canonical representation of a financial metric.

    This is the common structure used by both:
    - Bloomberg
    - Screener
    """

    name: str
    value: Optional[float]

    period: str

    currency: Optional[str] = None
    unit: Optional[str] = None

    source: Optional[str] = None
    source_field: Optional[str] = None
    source_sheet: Optional[str] = None
    source_row: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "period": self.period,
            "currency": self.currency,
            "unit": self.unit,
            "source": self.source,
            "source_field": self.source_field,
            "source_sheet": self.source_sheet,
            "source_row": self.source_row,
        }


CANONICAL_METRICS = {
    # Income Statement
    "revenue",
    "operating_expenses",
    "operating_profit",
    "ebitda",
    "depreciation",
    "finance_cost",
    "profit_before_tax",
    "tax",
    "net_profit",
    "other_income",

    # Balance Sheet
    "cash",
    "accounts_receivable",
    "inventory",
    "accounts_payable",
    "total_current_assets",
    "total_current_liabilities",
    "total_assets",
    "total_liabilities",
    "borrowings",
    "lease_liabilities",

    # Cash Flow
    "operating_cash_flow",
    "investing_cash_flow",
    "financing_cash_flow",
    "capital_expenditure",

    # Other
    "related_party_transactions",
    "contingent_liabilities",
}