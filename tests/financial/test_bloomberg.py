from backend.financial.sources.bloomberg import BloombergParser


FILE_PATH = "data/financial/bloomberg/BS.xlsx"


def test_bloomberg_workbook():

    parser = BloombergParser(FILE_PATH)

    sheets = parser.get_sheets()

    assert "BS" in sheets
    assert "IS" in sheets
    assert "CF" in sheets