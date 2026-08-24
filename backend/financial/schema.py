import pandas as pd

from backend.financial.schema import FinancialMetric


class BloombergParser:

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.workbook = pd.ExcelFile(file_path)

    def get_sheets(self) -> list[str]:
        return self.workbook.sheet_names

    def read_sheet(self, sheet_name: str) -> pd.DataFrame:
        return pd.read_excel(
            self.file_path,
            sheet_name=sheet_name,
            header=None
        )

    def load(self) -> dict[str, pd.DataFrame]:
        """
        Load the Bloomberg workbook sheets.

        Expected sheets:
        - BS
        - IS
        - CF
        """

        expected_sheets = {"BS", "IS", "CF"}

        actual_sheets = set(self.get_sheets())

        missing = expected_sheets - actual_sheets

        if missing:
            raise ValueError(
                f"Bloomberg file is missing sheets: {sorted(missing)}"
            )

        return {
            "BS": self.read_sheet("BS"),
            "IS": self.read_sheet("IS"),
            "CF": self.read_sheet("CF"),
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