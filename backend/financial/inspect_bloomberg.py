from pathlib import Path
from pprint import pprint

from backend.financial.sources.bloomberg import BloombergParser


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FILE_PATH = (
    PROJECT_ROOT
    / "data"
    / "financial"
    / "bloomberg"
    / "BS.xlsx"
)


def main():
    print("Starting Bloomberg inspection...")
    print(f"Looking for file: {FILE_PATH}")

    parser = BloombergParser(FILE_PATH)

    print("\n=== BLOOMBERG SHEETS ===")
    print(parser.get_sheets())

    print("\n=== BLOOMBERG INSPECTION ===")

    result = parser.inspect()

    for sheet, information in result.items():

        print(f"\n--- {sheet} ---")

        print("Rows:", information["rows"])
        print("Columns:", information["columns"])

        print("\nMetadata:")
        pprint(information["metadata"])

        print("\nFields found:")

        for field in information["fields"][:30]:
            print(field)


if __name__ == "__main__":
    main()