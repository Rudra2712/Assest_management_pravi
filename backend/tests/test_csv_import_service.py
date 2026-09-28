import pytest

from app.services.csv_import_service import REQUIRED_COLUMNS, parse_csv


def test_parse_csv_returns_rows_as_dicts():
    content = b"asset_code,name,asset_type_code,department_code,administrative_unit_code\nA1,Test,ROAD,RNB,DIV1\n"
    rows = parse_csv(content)
    assert rows == [{
        "asset_code": "A1", "name": "Test", "asset_type_code": "ROAD",
        "department_code": "RNB", "administrative_unit_code": "DIV1",
    }]


def test_parse_csv_is_case_insensitive_on_headers():
    content = b"Asset_Code,Name,Asset_Type_Code,Department_Code,Administrative_Unit_Code\nA1,Test,ROAD,RNB,DIV1\n"
    rows = parse_csv(content)
    assert rows[0]["asset_code"] == "A1"


def test_parse_csv_rejects_missing_required_columns():
    content = b"name,asset_type_code\nTest,ROAD\n"
    with pytest.raises(ValueError) as exc_info:
        parse_csv(content)
    for col in REQUIRED_COLUMNS:
        if col not in ("name", "asset_type_code"):
            assert col in str(exc_info.value)
