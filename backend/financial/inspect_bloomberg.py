from pathlib import Path

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

    for sheet, information in result["sheet_details"].items():

        print(f"\n--- {sheet} ---")

        print("Rows:", information["rows"])
        print("Columns:", information["columns"])

        print("\nMetadata:")
        print(information["metadata"])

        print("\nRows:")

        for index, row in enumerate(
            information["rows_text"],
            start=1,
        ):
            print(f"{index}: {row}")


if __name__ == "__main__":
    main()