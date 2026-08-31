from pathlib import Path
from pprint import pprint

from backend.financial.sources.screener import ScreenerParser


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FILE_PATH = (
    PROJECT_ROOT
    / "data"
    / "financial"
    / "screener"
    / "screener_export.xlsx"
)


def main():
    print("Starting Screener inspection...")
    print(f"Looking for file: {FILE_PATH}")

    parser = ScreenerParser(FILE_PATH)

    print("\n=== SCREENER SHEETS ===")
    print(parser.get_sheets())

    print("\n=== SCREENER INSPECTION ===")

    result = parser.inspect()

    for sheet, information in result["sheet_details"].items():

        print(f"\n--- {sheet} ---")

        print("Rows:", information["rows"])
        print("Columns:", information["columns"])

        print("\nFirst rows:")

        for row in information["first_rows"]:
            print(row)


if __name__ == "__main__":
    main()