"""Synchronous CSV asset import (no background worker for the MVP).

Flow: parse -> validate -> normalize -> duplicate detection -> (preview or
commit). Duplicates are always skipped, never overwritten, so an import can
never silently clobber existing government records.
"""

import io
import uuid
from datetime import date, datetime
from typing import Any

import pandas as pd

from app.models.asset import Asset, AssetType
from app.models.enums import AssetTypeCode, LifecycleStatus
from app.models.geo import AdministrativeUnit, Department
from app.models.user import User
from app.utils.audit import record_audit

REQUIRED_COLUMNS = ["asset_code", "name", "asset_type_code", "department_code", "administrative_unit_code"]
OPTIONAL_COLUMNS = [
    "ownership", "address", "lifecycle_status", "acquisition_date", "commissioning_date",
    "original_cost", "current_value", "useful_life_years", "lat", "lon",
]


def _parse_date(value: Any) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)) or value == "":
        return None
    if isinstance(value, str):
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    return None


def _clean(value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return value


def parse_csv(content: bytes) -> list[dict]:
    df = pd.read_csv(io.BytesIO(content), dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
    return df.to_dict(orient="records")


def validate_and_preview(db, rows: list[dict]) -> dict:
    departments = {d.code: d for d in db.query(Department).all()}
    admin_units = {u.code: u for u in db.query(AdministrativeUnit).all()}
    asset_types = {t.code.value: t for t in db.query(AssetType).all()}
    existing_codes = {a.asset_code for a in db.query(Asset.asset_code).all()}

    results = []
    for idx, row in enumerate(rows, start=2):  # account for header row
        errors = []
        asset_code = (row.get("asset_code") or "").strip()
        name = (row.get("name") or "").strip()
        asset_type_code = (row.get("asset_type_code") or "").strip().upper()
        department_code = (row.get("department_code") or "").strip()
        administrative_unit_code = (row.get("administrative_unit_code") or "").strip()

        if not asset_code:
            errors.append("asset_code is required")
        if not name:
            errors.append("name is required")
        if asset_type_code not in asset_types:
            errors.append(f"unknown asset_type_code '{asset_type_code}'")
        if department_code not in departments:
            errors.append(f"unknown department_code '{department_code}'")
        if administrative_unit_code not in admin_units:
            errors.append(f"unknown administrative_unit_code '{administrative_unit_code}'")

        is_duplicate = asset_code in existing_codes

        results.append({
            "row_number": idx,
            "asset_code": asset_code,
            "name": name,
            "is_duplicate": is_duplicate,
            "errors": errors,
            "importable": not errors and not is_duplicate,
            "raw": row,
        })

    return {
        "total_rows": len(results),
        "importable_count": sum(1 for r in results if r["importable"]),
        "duplicate_count": sum(1 for r in results if r["is_duplicate"]),
        "error_count": sum(1 for r in results if r["errors"]),
        "rows": results,
    }


def commit_import(db, rows: list[dict], user: User) -> dict:
    preview = validate_and_preview(db, rows)
    departments = {d.code: d for d in db.query(Department).all()}
    admin_units = {u.code: u for u in db.query(AdministrativeUnit).all()}
    asset_types = {t.code.value: t for t in db.query(AssetType).all()}

    imported = 0
    for row in preview["rows"]:
        if not row["importable"]:
            continue
        raw = row["raw"]
        asset = Asset(
            asset_code=row["asset_code"],
            name=row["name"],
            asset_type_id=asset_types[raw["asset_type_code"].strip().upper()].id,
            department_id=departments[raw["department_code"].strip()].id,
            administrative_unit_id=admin_units[raw["administrative_unit_code"].strip()].id,
            ownership=_clean(raw.get("ownership")),
            address=_clean(raw.get("address")),
            lifecycle_status=LifecycleStatus(raw["lifecycle_status"].strip().upper()) if _clean(raw.get("lifecycle_status")) else LifecycleStatus.PLANNED,
            acquisition_date=_parse_date(raw.get("acquisition_date")),
            commissioning_date=_parse_date(raw.get("commissioning_date")),
            original_cost=float(raw["original_cost"]) if _clean(raw.get("original_cost")) else None,
            current_value=float(raw["current_value"]) if _clean(raw.get("current_value")) else None,
            useful_life_years=int(float(raw["useful_life_years"])) if _clean(raw.get("useful_life_years")) else None,
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(asset)
        imported += 1

    record_audit(
        db, actor_id=user.id, action="CSV_IMPORT", entity_type="csv_import_batch", entity_id=uuid.uuid4(),
        new_value={"imported": imported, "skipped_duplicates": preview["duplicate_count"], "skipped_errors": preview["error_count"]},
    )

    return {"imported": imported, "skipped_duplicates": preview["duplicate_count"], "skipped_errors": preview["error_count"]}
