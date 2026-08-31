from pathlib import Path

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

    parser = ScreenerParser(FILE_PATH)

    print("\n=== COMPANY ===")
    print(parser.get_company_name())

    print("\n=== EXTRACTED METRICS ===")

    metrics = parser.extract_metrics()

    print(f"Total metrics extracted: {len(metrics)}")

    for metric in metrics[:30]:
        print(metric.to_dict())


if __name__ == "__main__":
    main()