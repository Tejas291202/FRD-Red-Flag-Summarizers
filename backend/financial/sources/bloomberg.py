from pathlib import Path
from typing import Any

import pandas as pd


class BloombergParser:
    """
    Parser and inspection utility for Bloomberg Excel exports.

    V1 focuses on safely loading and inspecting Bloomberg
    worksheets. Financial field mappings will be added only
    after the actual workbook structure has been verified.
    """

    EXPECTED_SHEETS = ("BS", "IS", "CF")

    SOURCE_NAME = "Bloomberg"

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Bloomberg file not found: {self.file_path}"
            )

        if self.file_path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError(
                "Bloomberg input must be an Excel file (.xlsx or .xls)."
            )

        self.workbook = pd.ExcelFile(self.file_path)

    # =========================================================
    # Workbook
    # =========================================================

    def get_sheets(self) -> list[str]:
        """Return all worksheet names."""

        return self.workbook.sheet_names

    def validate_workbook(self) -> None:
        """Validate that expected Bloomberg sheets exist."""

        actual_sheets = set(self.get_sheets())
        missing = set(self.EXPECTED_SHEETS) - actual_sheets

        if missing:
            raise ValueError(
                "Invalid Bloomberg workbook. "
                f"Missing sheets: {sorted(missing)}"
            )

    def read_sheet(self, sheet_name: str) -> pd.DataFrame:
        """Read a Bloomberg worksheet without assuming headers."""

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

    # =========================================================
    # Safe cell conversion
    # =========================================================

    @staticmethod
    def safe_text(value: Any) -> str:
        """
        Safely convert any Excel cell to text.

        Handles:
            strings
            numbers
            dates
            NaN
            None
        """

        if pd.isna(value):
            return ""

        return str(value).strip()

    @classmethod
    def row_to_text(cls, row) -> str:
        """Convert a complete worksheet row into safe text."""

        values = []

        for cell in row:

            text = cls.safe_text(cell)

            if text:
                values.append(text)

        return " | ".join(values)

    # =========================================================
    # Metadata
    # =========================================================

    def detect_metadata(self, df: pd.DataFrame) -> dict[str, Any]:
        """
        Safely inspect worksheet cells for common metadata.

        This method deliberately does not make assumptions about
        Bloomberg's exact workbook layout.
        """

        metadata = {
            "company": None,
            "currency": None,
            "unit": None,
        }

        for _, row in df.iterrows():

            for cell in row:

                cell_text = self.safe_text(cell)

                if not cell_text:
                    continue

                upper_text = cell_text.upper()
                lower_text = cell_text.lower()

                # Company
                if metadata["company"] is None:

                    if any(
                        term in cell_text
                        for term in (
                            "Ltd",
                            "Limited",
                            "Corporation",
                            "Corp",
                            "Inc.",
                        )
                    ):
                        metadata["company"] = cell_text

                # Currency
                if metadata["currency"] is None:

                    if "INR" in upper_text:
                        metadata["currency"] = "INR"

                    elif "USD" in upper_text:
                        metadata["currency"] = "USD"

                    elif "EUR" in upper_text:
                        metadata["currency"] = "EUR"

                    elif "GBP" in upper_text:
                        metadata["currency"] = "GBP"

                # Unit
                if metadata["unit"] is None:

                    if "billion" in lower_text:
                        metadata["unit"] = "billion"

                    elif "million" in lower_text:
                        metadata["unit"] = "million"

                    elif "crore" in lower_text:
                        metadata["unit"] = "crore"

        return metadata

    # =========================================================
    # Inspection
    # =========================================================

    def inspect_sheet(self, sheet_name: str) -> dict[str, Any]:
        """Inspect one Bloomberg worksheet."""

        df = self.read_sheet(sheet_name)

        rows = []

        for _, row in df.iterrows():
            rows.append(self.row_to_text(row))

        return {
            "sheet": sheet_name,
            "rows": len(df),
            "columns": len(df.columns),
            "metadata": self.detect_metadata(df),
            "rows_text": rows,
        }

    def inspect(self) -> dict[str, Any]:
        """
        Inspect the complete Bloomberg workbook.
        """

        self.validate_workbook()

        result = {
            "file": str(self.file_path),
            "sheets": self.get_sheets(),
            "sheet_details": {},
        }

        for sheet in self.EXPECTED_SHEETS:

            result["sheet_details"][sheet] = (
                self.inspect_sheet(sheet)
            )

        return result