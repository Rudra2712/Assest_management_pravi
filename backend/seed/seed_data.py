"""Synthetic demo data for the hackathon presentation. None of this represents
real government records — asset names reference real Gujarat geography
(Sabarmati, Tapi, Mahi, Aji, Shetrunji, Nagmati rivers; real city names) for
plausibility, but every asset, person and figure here is fictional.

Run with:

    cd backend
    python -m seed.seed_data

Safe to re-run: reference data (departments, admin hierarchy, roles, the 8
demo user accounts, asset types, contractors) is upserted in place; business
data (assets and everything hanging off them, grievances, tenders, projects)
is cleared and regenerated fresh each run so the dataset stays internally
consistent rather than accumulating duplicates.
"""

import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models.asset import Asset, AssetCategory, AssetType
from app.models.condition import ConditionAssessment
from app.models.contractor import Contractor
from app.models.enums import (
    AdminUnitLevel,
    AssetTypeCode,
    ConditionRating,
    FindingSeverity,
    GeometryKind,
    GrievanceCategory,
    GrievanceStatus,
    InspectionStatus,
    LifecycleStatus,
    MaintenancePriority,
    MaintenanceRequestStatus,
    MaintenanceType,
    NotificationEvent,
    ProjectStatus,
    SystemRole,
    TenderBidStatus,
    TenderStatus,
    WorkOrderStatus,
)
from app.models.geo import AdministrativeUnit, Department
from app.models.grievance import Grievance
from app.models.inspection import Inspection, InspectionFinding
from app.models.maintenance import MaintenanceRecord, MaintenanceRequest, WorkOrder
from app.models.notification import Notification
from app.models.project import Project, ProjectAsset
from app.models.tender import Tender, TenderBid
from app.models.user import Role, User, UserRole
from app.schemas.asset import AssetCreate, BridgeDetail, BuildingDetail, CulvertDetail, RoadDetail, StructureDetail
from app.services import asset_service
from app.services.condition_service import compute_condition
from app.services.lifecycle_service import transition_asset

DEMO_PASSWORD = "Password123!"
RNG = random.Random(42)

BASE_CHAIN = [LifecycleStatus.SANCTIONED, LifecycleStatus.UNDER_CONSTRUCTION, LifecycleStatus.COMMISSIONED, LifecycleStatus.OPERATIONAL]


def advance_to(db, asset: Asset, user: User, target: LifecycleStatus, reason: str = "Seed data") -> None:
    """Walks the lifecycle state machine from PLANNED to `target`, writing a
    real lifecycle_events row at each hop (never jumps straight there)."""
    if target == LifecycleStatus.PLANNED:
        return
    if target in BASE_CHAIN:
        for status in BASE_CHAIN[: BASE_CHAIN.index(target) + 1]:
            transition_asset(db, asset, status, user, reason)
    else:
        for status in BASE_CHAIN:
            transition_asset(db, asset, status, user, reason)
        transition_asset(db, asset, target, user, reason)


# ---------------------------------------------------------------------------
# Reference data (idempotent — safe to upsert on every run)
# ---------------------------------------------------------------------------

def upsert_department(db) -> Department:
    dept = db.query(Department).filter(Department.code == "RNB").first()
    if not dept:
        dept = Department(code="RNB", name="Roads & Buildings Department", description="R&B Department (demo data)")
        db.add(dept)
        db.flush()
    return dept


def upsert_admin_unit(db, code, name, level, parent: AdministrativeUnit | None) -> AdministrativeUnit:
    unit = db.query(AdministrativeUnit).filter(AdministrativeUnit.code == code).first()
    if unit:
        unit.name = name
        unit.level = level
        unit.parent_id = parent.id if parent else None
        unit.path = f"{parent.path}.{unit.id}" if parent else str(unit.id)
        return unit
    unit = AdministrativeUnit(code=code, name=name, level=level, parent_id=parent.id if parent else None, path="")
    db.add(unit)
    db.flush()
    unit.path = f"{parent.path}.{unit.id}" if parent else str(unit.id)
    return unit


def upsert_roles(db) -> dict[str, Role]:
    roles = {}
    for role in SystemRole:
        existing = db.query(Role).filter(Role.code == role.value).first()
        if not existing:
            existing = Role(code=role.value, name=role.value.replace("_", " ").title(), is_system_role=True)
            db.add(existing)
            db.flush()
        roles[role.value] = existing
    return roles


def upsert_user(db, email, full_name, dept, unit, roles: list[Role], jurisdiction_unit=None) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.full_name = full_name
        user.department_id = dept.id if dept else None
        user.administrative_unit_id = unit.id if unit else None
        user.is_active = True
        for grant in list(user.role_grants):
            db.delete(grant)
        db.flush()
        for role in roles:
            db.add(UserRole(user_id=user.id, role_id=role.id, jurisdiction_unit_id=unit.id if unit else None))
        return user
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(DEMO_PASSWORD),
        department_id=dept.id if dept else None,
        administrative_unit_id=unit.id if unit else None,
    )
    db.add(user)
    db.flush()
    for role in roles:
        db.add(UserRole(user_id=user.id, role_id=role.id, jurisdiction_unit_id=(jurisdiction_unit or unit).id if (jurisdiction_unit or unit) else None))
    return user


def upsert_asset_category(db) -> AssetCategory:
    cat = db.query(AssetCategory).filter(AssetCategory.code == "INFRA").first()
    if not cat:
        cat = AssetCategory(code="INFRA", name="Infrastructure")
        db.add(cat)
        db.flush()
    return cat


def upsert_asset_types(db, category: AssetCategory) -> dict[str, AssetType]:
    defs = [
        (AssetTypeCode.ROAD, "Road", GeometryKind.LINESTRING),
        (AssetTypeCode.BRIDGE, "Bridge", GeometryKind.POINT),
        (AssetTypeCode.CULVERT, "Culvert", GeometryKind.POINT),
        (AssetTypeCode.BUILDING, "Building", GeometryKind.POLYGON),
        (AssetTypeCode.PUBLIC_STRUCTURE, "Public Structure", GeometryKind.POINT),
        (AssetTypeCode.OTHER_FIXED_ASSET, "Other Fixed Asset", GeometryKind.POINT),
    ]
    result = {}
    for code, name, geom_kind in defs:
        existing = db.query(AssetType).filter(AssetType.code == code).first()
        if not existing:
            existing = AssetType(code=code, name=name, default_geometry_kind=geom_kind, category_id=category.id)
            db.add(existing)
            db.flush()
        result[code.value] = existing
    return result


def upsert_contractor(db, name, reg_no, contact_person="Site Manager", phone="9800000000") -> Contractor:
    existing = db.query(Contractor).filter(Contractor.registration_number == reg_no).first()
    if existing:
        return existing
    c = Contractor(name=name, registration_number=reg_no, contact_person=contact_person, phone=phone, email=f"{reg_no.lower()}@example.com")
    db.add(c)
    db.flush()
    return c


# ---------------------------------------------------------------------------
# Business data wipe — assets/grievances/tenders/projects only. Reference
# data (departments, admin units, roles, users, asset types, contractors)
# is left alone so logins and jurisdiction assignments never change.
# ---------------------------------------------------------------------------

def clear_business_data(db) -> None:
    db.execute(text("DELETE FROM contractor_assignments"))
    db.execute(text("UPDATE tenders SET awarded_bid_id = NULL"))
    db.execute(text("DELETE FROM tender_bids"))
    db.execute(text("DELETE FROM tenders"))
    db.execute(text("DELETE FROM grievances"))
    db.execute(text("DELETE FROM notifications"))
    db.execute(text("DELETE FROM audit_logs"))
    # work_orders.asset_id is a direct (non-cascading) FK to assets, separate
    # from its maintenance_request_id path — must clear it explicitly before
    # deleting assets, or Postgres blocks the delete even though the
    # maintenance_request_id path alone would have cascaded fine.
    db.execute(text("DELETE FROM maintenance_records"))
    db.execute(text("DELETE FROM work_orders"))
    db.execute(text("DELETE FROM maintenance_requests"))
    db.execute(text("DELETE FROM assets"))  # cascades geometry/details/lifecycle/inspections/condition assessments
    db.execute(text("DELETE FROM projects"))
    db.commit()


# ---------------------------------------------------------------------------
# City / admin-hierarchy data — six real Gujarat cities, each its own division.
# ---------------------------------------------------------------------------

CITIES = {
    "ahmedabad": dict(
        name="Ahmedabad", circle_code="CIR-N", circle_name="North Gujarat Circle",
        div_code="DIV-N1", div_name="Ahmedabad Division", sd_code="SD-N1A", sd_name="Ahmedabad Sub-Division",
        center=(72.5714, 23.0225),
    ),
    "surat": dict(
        name="Surat", circle_code="CIR-C", circle_name="South-Central Gujarat Circle",
        div_code="DIV-C2", div_name="Surat Division", sd_code="SD-C2A", sd_name="Surat Sub-Division",
        center=(72.8311, 21.1702),
    ),
    "vadodara": dict(
        name="Vadodara", circle_code="CIR-C", circle_name="South-Central Gujarat Circle",
        div_code="DIV-C3", div_name="Vadodara Division", sd_code="SD-C3A", sd_name="Vadodara Sub-Division",
        center=(73.1812, 22.3072),
    ),
    "rajkot": dict(
        name="Rajkot", circle_code="CIR-S", circle_name="Saurashtra-Kutch Circle",
        div_code="DIV-S1", div_name="Rajkot Division", sd_code="SD-S1A", sd_name="Rajkot Sub-Division",
        center=(70.8022, 22.3039),
    ),
    "bhavnagar": dict(
        name="Bhavnagar", circle_code="CIR-S", circle_name="Saurashtra-Kutch Circle",
        div_code="DIV-S4", div_name="Bhavnagar Division", sd_code="SD-S4A", sd_name="Bhavnagar Sub-Division",
        center=(72.1519, 21.7645),
    ),
    "jamnagar": dict(
        name="Jamnagar", circle_code="CIR-S", circle_name="Saurashtra-Kutch Circle",
        div_code="DIV-S5", div_name="Jamnagar Division", sd_code="SD-S5A", sd_name="Jamnagar Sub-Division",
        center=(70.0577, 22.4707),
    ),
}


def build_admin_hierarchy(db) -> dict:
    state = upsert_admin_unit(db, "ST", "State of Gujarat", AdminUnitLevel.STATE, None)
    circles: dict[str, AdministrativeUnit] = {}
    units = {"state": state}
    for key, c in CITIES.items():
        circle = circles.get(c["circle_code"])
        if not circle:
            circle = upsert_admin_unit(db, c["circle_code"], c["circle_name"], AdminUnitLevel.REGION_CIRCLE, state)
            circles[c["circle_code"]] = circle
        division = upsert_admin_unit(db, c["div_code"], c["div_name"], AdminUnitLevel.DIVISION, circle)
        sub_division = upsert_admin_unit(db, c["sd_code"], c["sd_name"], AdminUnitLevel.SUB_DIVISION, division)
        units[key] = {"circle": circle, "division": division, "sub_division": sub_division}
    # Field section kept for backward-compat continuity with earlier seed runs.
    upsert_admin_unit(db, "SEC-N1A1", "Ahmedabad East Field Section", AdminUnitLevel.SECTION_FIELD_OFFICE, units["ahmedabad"]["sub_division"])
    return units


# ---------------------------------------------------------------------------
# Asset catalogue — realistic Gujarat infrastructure per city.
# ---------------------------------------------------------------------------

def _line(cx, cy, *offsets) -> dict:
    coords = [[cx, cy]] + [[cx + dx, cy + dy] for dx, dy in offsets]
    return {"type": "LineString", "coordinates": coords}


def _point(cx, cy, dx=0.0, dy=0.0) -> dict:
    return {"type": "Point", "coordinates": [cx + dx, cy + dy]}


def _rect(cx, cy, half=0.0006) -> dict:
    return {"type": "Polygon", "coordinates": [[
        [cx - half, cy - half], [cx + half, cy - half], [cx + half, cy + half], [cx - half, cy + half], [cx - half, cy - half],
    ]]}


def build_asset_catalogue(units: dict) -> list[dict]:
    """One entry per asset. `lifecycle` is the target end-state (walked there
    via advance_to); `condition` is applied directly once OPERATIONAL-ish."""

    catalogue: list[dict] = []

    def add(**kwargs):
        catalogue.append(kwargs)

    # ---- Ahmedabad (Sabarmati) ------------------------------------------------
    cx, cy = CITIES["ahmedabad"]["center"]
    sd, div = units["ahmedabad"]["sub_division"], units["ahmedabad"]["division"]
    add(code="RB-ROAD-0001", name="SH-12 Ahmedabad Bypass", type=AssetTypeCode.ROAD, unit=sd, city="Ahmedabad",
        geometry=_line(cx - 0.07, cy - 0.02, (0.05, 0.01), (0.06, 0.05)),
        detail=RoadDetail(length_km=12.4, width_m=7.0, number_of_lanes=2, surface_type="Bituminous", start_point_desc="Junction KM 0", end_point_desc="Northern Toll Plaza"),
        commissioning=date(2015, 6, 1), cost=8_000_000, life=20, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)
    add(code="RB-ROAD-0002", name="Sabarmati Riverfront Connector", type=AssetTypeCode.ROAD, unit=sd, city="Ahmedabad",
        geometry=_line(cx + 0.01, cy - 0.02, (0.02, 0.0)),
        detail=RoadDetail(length_km=6.1, width_m=10.0, number_of_lanes=4, surface_type="Bituminous (under widening)"),
        commissioning=None, cost=45_000_000, life=25, lifecycle=LifecycleStatus.UNDER_CONSTRUCTION, condition=None,
        project_key="ahmedabad_connector")
    add(code="RB-ROAD-0003", name="Ahmedabad-Gandhinagar Highway (SH-1A)", type=AssetTypeCode.ROAD, unit=div, city="Ahmedabad",
        geometry=_line(cx + 0.03, cy + 0.15, (0.02, 0.05), (0.01, 0.08)),
        detail=RoadDetail(length_km=23.0, width_m=14.0, number_of_lanes=6, surface_type="Bituminous", traffic_info="High-density commuter corridor"),
        commissioning=date(2009, 1, 1), cost=28_000_000, life=20, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-BRIDGE-0001", name="Sabarmati River Bridge", type=AssetTypeCode.BRIDGE, unit=sd, city="Ahmedabad",
        geometry=_point(cx, cy),
        detail=BridgeDetail(length_m=180, width_m=9, number_of_spans=3, bridge_type="Girder", material="RCC", load_capacity_tonnes=40),
        commissioning=date(2005, 3, 1), cost=15_000_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.POOR)
    add(code="RB-BRIDGE-0003", name="Vasna Barrage Bridge", type=AssetTypeCode.BRIDGE, unit=sd, city="Ahmedabad",
        geometry=_point(cx - 0.04, cy - 0.11),
        detail=BridgeDetail(length_m=210, width_m=11, number_of_spans=4, bridge_type="Girder", material="RCC", load_capacity_tonnes=45),
        commissioning=date(2011, 9, 1), cost=19_500_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-CULVERT-0001", name="Sabarmati Canal Culvert", type=AssetTypeCode.CULVERT, unit=sd, city="Gandhinagar",
        geometry=_point(72.6369, 23.2156),
        detail=CulvertDetail(culvert_type="Box Culvert", length_m=6, opening_width_m=2.5, material="RCC"),
        commissioning=date(2012, 1, 1), cost=400_000, life=25, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-CULVERT-0002", name="Chandola Lake Outfall Culvert", type=AssetTypeCode.CULVERT, unit=sd, city="Ahmedabad",
        geometry=_point(cx + 0.02, cy - 0.05),
        detail=CulvertDetail(culvert_type="Slab Culvert", length_m=4, opening_width_m=1.8, material="RCC"),
        commissioning=date(2008, 6, 1), cost=280_000, life=25, lifecycle=LifecycleStatus.MAINTENANCE_REQUIRED, condition=ConditionRating.POOR)
    add(code="RB-BLDG-0001", name="Ahmedabad Divisional Office", type=AssetTypeCode.BUILDING, unit=div, city="Ahmedabad",
        geometry=_rect(cx - 0.001, cy + 0.001),
        detail=BuildingDetail(plot_area_sqm=1200, built_up_area_sqm=650, number_of_floors=2, construction_year=1998, building_type="Office", occupancy_use="Divisional administrative office"),
        commissioning=date(1998, 4, 1), cost=3_500_000, life=50, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-BLDG-0003", name="Naranpura PWD Rest House", type=AssetTypeCode.BUILDING, unit=sd, city="Ahmedabad",
        geometry=_rect(cx + 0.015, cy + 0.02),
        detail=BuildingDetail(plot_area_sqm=500, built_up_area_sqm=220, number_of_floors=1, construction_year=2014, building_type="Rest House", occupancy_use="Field staff accommodation"),
        commissioning=date(2014, 2, 1), cost=1_100_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-STRUCT-0001", name="Ahmedabad Traffic Circle Monument", type=AssetTypeCode.PUBLIC_STRUCTURE, unit=div, city="Ahmedabad",
        geometry=_point(cx + 0.0026, cy + 0.0025),
        detail=StructureDetail(structure_subtype="Monument", attributes={"height_m": 6}),
        commissioning=date(2001, 1, 1), cost=350_000, life=30, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)

    # ---- Surat (Tapi) ----------------------------------------------------------
    cx, cy = CITIES["surat"]["center"]
    sd, div = units["surat"]["sub_division"], units["surat"]["division"]
    add(code="RB-ROAD-0004", name="NH-48 Surat Bypass", type=AssetTypeCode.ROAD, unit=sd, city="Surat",
        geometry=_line(cx - 0.08, cy - 0.03, (0.06, 0.02), (0.07, 0.06)),
        detail=RoadDetail(length_km=18.6, width_m=15.0, number_of_lanes=6, surface_type="Bituminous", traffic_info="National highway segment"),
        commissioning=date(2013, 1, 1), cost=32_000_000, life=20, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-ROAD-0005", name="Surat Ring Road (Ph. 2)", type=AssetTypeCode.ROAD, unit=div, city="Surat",
        geometry=_line(cx + 0.02, cy + 0.03, (0.03, 0.02)),
        detail=RoadDetail(length_km=9.2, width_m=12.0, number_of_lanes=4, surface_type="Bituminous"),
        commissioning=None, cost=21_000_000, life=20, lifecycle=LifecycleStatus.SANCTIONED, condition=None,
        project_key="surat_ring_road")
    add(code="RB-BRIDGE-0004", name="Tapi River Bridge (Nehru Bridge Link)", type=AssetTypeCode.BRIDGE, unit=sd, city="Surat",
        geometry=_point(cx, cy),
        detail=BridgeDetail(length_m=340, width_m=13, number_of_spans=6, bridge_type="Girder", material="RCC", load_capacity_tonnes=50),
        commissioning=date(1998, 11, 1), cost=26_000_000, life=45, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)
    add(code="RB-CULVERT-0003", name="Athwalines Storm Water Culvert", type=AssetTypeCode.CULVERT, unit=sd, city="Surat",
        geometry=_point(cx - 0.02, cy + 0.015),
        detail=CulvertDetail(culvert_type="Box Culvert", length_m=8, opening_width_m=3.0, material="RCC"),
        commissioning=date(2016, 5, 1), cost=520_000, life=25, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-BLDG-0004", name="Surat Circuit House", type=AssetTypeCode.BUILDING, unit=div, city="Surat",
        geometry=_rect(cx + 0.01, cy - 0.01),
        detail=BuildingDetail(plot_area_sqm=1500, built_up_area_sqm=780, number_of_floors=2, construction_year=2002, building_type="Guest House", occupancy_use="Visiting officers' circuit house"),
        commissioning=date(2002, 3, 1), cost=4_200_000, life=50, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)

    # ---- Vadodara (Vishwamitri) --------------------------------------------
    cx, cy = CITIES["vadodara"]["center"]
    sd, div = units["vadodara"]["sub_division"], units["vadodara"]["division"]
    add(code="RB-ROAD-0006", name="Vadodara-Halol Expressway Link Road", type=AssetTypeCode.ROAD, unit=sd, city="Vadodara",
        geometry=_line(cx, cy - 0.02, (0.05, 0.08), (0.09, 0.14)),
        detail=RoadDetail(length_km=15.8, width_m=12.0, number_of_lanes=4, surface_type="Bituminous"),
        commissioning=None, cost=34_000_000, life=20, lifecycle=LifecycleStatus.UNDER_CONSTRUCTION, condition=None,
        project_key="vadodara_expressway")
    add(code="RB-BRIDGE-0005", name="Vishwamitri River Bridge", type=AssetTypeCode.BRIDGE, unit=sd, city="Vadodara",
        geometry=_point(cx - 0.015, cy + 0.01),
        detail=BridgeDetail(length_m=160, width_m=10, number_of_spans=3, bridge_type="Girder", material="RCC", load_capacity_tonnes=38),
        commissioning=date(2007, 7, 1), cost=13_800_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)
    add(code="RB-CULVERT-0004", name="Ajwa Road Culvert", type=AssetTypeCode.CULVERT, unit=sd, city="Vadodara",
        geometry=_point(cx + 0.025, cy - 0.02),
        detail=CulvertDetail(culvert_type="Pipe Culvert", length_m=5, opening_width_m=1.5, material="RCC"),
        commissioning=date(2010, 4, 1), cost=210_000, life=20, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-BLDG-0005", name="Vadodara PWD Office", type=AssetTypeCode.BUILDING, unit=div, city="Vadodara",
        geometry=_rect(cx, cy + 0.005),
        detail=BuildingDetail(plot_area_sqm=1100, built_up_area_sqm=600, number_of_floors=3, construction_year=1995, building_type="Office", occupancy_use="Divisional office"),
        commissioning=date(1995, 1, 1), cost=3_100_000, life=50, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)

    # ---- Rajkot (Aji) --------------------------------------------------------
    cx, cy = CITIES["rajkot"]["center"]
    sd, div = units["rajkot"]["sub_division"], units["rajkot"]["division"]
    add(code="RB-ROAD-0007", name="Rajkot Ring Road", type=AssetTypeCode.ROAD, unit=sd, city="Rajkot",
        geometry=_line(cx - 0.06, cy - 0.04, (0.05, 0.03), (0.08, 0.01)),
        detail=RoadDetail(length_km=14.0, width_m=10.0, number_of_lanes=4, surface_type="Bituminous"),
        commissioning=date(2011, 3, 1), cost=17_500_000, life=20, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-ROAD-0008", name="Nyari Dam Approach Road", type=AssetTypeCode.ROAD, unit=sd, city="Rajkot",
        geometry=_line(cx + 0.03, cy + 0.06, (0.02, 0.03)),
        detail=RoadDetail(length_km=5.4, width_m=6.0, number_of_lanes=2, surface_type="WBM"),
        commissioning=date(1992, 1, 1), cost=1_800_000, life=15, lifecycle=LifecycleStatus.MAINTENANCE_REQUIRED, condition=ConditionRating.POOR)
    add(code="RB-BRIDGE-0002", name="Aji River Bridge", type=AssetTypeCode.BRIDGE, unit=sd, city="Rajkot",
        geometry=_point(cx, cy),
        detail=BridgeDetail(length_m=45, width_m=4, number_of_spans=2, bridge_type="Timber Truss", material="Timber", load_capacity_tonnes=8),
        commissioning=date(1985, 1, 1), cost=2_000_000, life=35, lifecycle=LifecycleStatus.MAINTENANCE_REQUIRED, condition=ConditionRating.CRITICAL)
    add(code="RB-CULVERT-0005", name="Bhichari Culvert", type=AssetTypeCode.CULVERT, unit=sd, city="Rajkot",
        geometry=_point(cx - 0.02, cy + 0.03),
        detail=CulvertDetail(culvert_type="Box Culvert", length_m=5, opening_width_m=2.0, material="RCC"),
        commissioning=date(2005, 8, 1), cost=190_000, life=25, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)
    add(code="RB-BLDG-0002", name="Rajkot Sub-Division Rest House", type=AssetTypeCode.BUILDING, unit=sd, city="Rajkot",
        geometry=_rect(cx - 0.0025, cy - 0.003),
        detail=BuildingDetail(plot_area_sqm=400, built_up_area_sqm=180, number_of_floors=1, construction_year=2010, building_type="Rest House", occupancy_use="Field staff accommodation"),
        commissioning=date(2010, 8, 1), cost=900_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-STRUCT-0002", name="Rajkot Race Course Gate Monument", type=AssetTypeCode.PUBLIC_STRUCTURE, unit=div, city="Rajkot",
        geometry=_point(cx + 0.004, cy - 0.004),
        detail=StructureDetail(structure_subtype="Gate/Monument", attributes={"height_m": 4}),
        commissioning=date(1970, 1, 1), cost=90_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)

    # ---- Bhavnagar (Shetrunji / port) --------------------------------------
    cx, cy = CITIES["bhavnagar"]["center"]
    sd, div = units["bhavnagar"]["sub_division"], units["bhavnagar"]["division"]
    add(code="RB-ROAD-0009", name="Bhavnagar Port Road", type=AssetTypeCode.ROAD, unit=sd, city="Bhavnagar",
        geometry=_line(cx - 0.03, cy - 0.02, (0.04, 0.03)),
        detail=RoadDetail(length_km=8.7, width_m=9.0, number_of_lanes=2, surface_type="Bituminous", traffic_info="Heavy freight traffic to port"),
        commissioning=date(2003, 6, 1), cost=6_400_000, life=20, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)
    add(code="RB-BRIDGE-0006", name="Shetrunji River Bridge", type=AssetTypeCode.BRIDGE, unit=sd, city="Bhavnagar",
        geometry=_point(cx, cy),
        detail=BridgeDetail(length_m=120, width_m=8, number_of_spans=2, bridge_type="Girder", material="RCC", load_capacity_tonnes=32),
        commissioning=date(1999, 2, 1), cost=9_200_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)
    add(code="RB-CULVERT-0006", name="Ghogha Jetty Approach Culvert", type=AssetTypeCode.CULVERT, unit=sd, city="Bhavnagar",
        geometry=_point(cx + 0.02, cy - 0.01),
        detail=CulvertDetail(culvert_type="Box Culvert", length_m=6, opening_width_m=2.2, material="RCC"),
        commissioning=date(2018, 1, 1), cost=310_000, life=25, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-BLDG-0006", name="Bhavnagar PWD Guest House", type=AssetTypeCode.BUILDING, unit=div, city="Bhavnagar",
        geometry=_rect(cx - 0.001, cy + 0.002),
        detail=BuildingDetail(plot_area_sqm=380, built_up_area_sqm=160, number_of_floors=1, construction_year=2006, building_type="Guest House", occupancy_use="Field staff accommodation"),
        commissioning=date(2006, 9, 1), cost=850_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)

    # ---- Jamnagar (Nagmati / refinery belt) --------------------------------
    cx, cy = CITIES["jamnagar"]["center"]
    sd, div = units["jamnagar"]["sub_division"], units["jamnagar"]["division"]
    add(code="RB-ROAD-0010", name="Jamnagar Refinery Road (SH-6)", type=AssetTypeCode.ROAD, unit=sd, city="Jamnagar",
        geometry=_line(cx - 0.05, cy + 0.01, (0.06, -0.02), (0.09, -0.05)),
        detail=RoadDetail(length_km=21.3, width_m=11.0, number_of_lanes=4, surface_type="Bituminous", traffic_info="Heavy industrial/tanker traffic"),
        commissioning=date(2000, 1, 1), cost=19_000_000, life=20, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)
    add(code="RB-BRIDGE-0007", name="Nagmati River Bridge", type=AssetTypeCode.BRIDGE, unit=sd, city="Jamnagar",
        geometry=_point(cx, cy),
        detail=BridgeDetail(length_m=95, width_m=7, number_of_spans=2, bridge_type="Girder", material="RCC", load_capacity_tonnes=30),
        commissioning=date(2014, 10, 1), cost=8_600_000, life=40, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.GOOD)
    add(code="RB-CULVERT-0007", name="Bedi Port Culvert", type=AssetTypeCode.CULVERT, unit=sd, city="Jamnagar",
        geometry=_point(cx + 0.015, cy + 0.02),
        detail=CulvertDetail(culvert_type="Box Culvert", length_m=7, opening_width_m=2.5, material="RCC"),
        commissioning=date(2009, 3, 1), cost=330_000, life=25, lifecycle=LifecycleStatus.MAINTENANCE_REQUIRED, condition=ConditionRating.POOR)
    add(code="RB-BLDG-0007", name="Jamnagar Circuit House", type=AssetTypeCode.BUILDING, unit=div, city="Jamnagar",
        geometry=_rect(cx - 0.002, cy - 0.001),
        detail=BuildingDetail(plot_area_sqm=900, built_up_area_sqm=480, number_of_floors=2, construction_year=1990, building_type="Guest House", occupancy_use="Visiting officers' circuit house"),
        commissioning=date(1990, 1, 1), cost=2_600_000, life=50, lifecycle=LifecycleStatus.OPERATIONAL, condition=ConditionRating.FAIR)

    return catalogue


DETAIL_FIELD = {
    AssetTypeCode.ROAD: "road", AssetTypeCode.BRIDGE: "bridge", AssetTypeCode.CULVERT: "culvert",
    AssetTypeCode.BUILDING: "building", AssetTypeCode.PUBLIC_STRUCTURE: "structure", AssetTypeCode.OTHER_FIXED_ASSET: "structure",
}


def create_assets(db, dept: Department, catalogue: list[dict], state_admin: User, projects: dict[str, Project]) -> dict[str, Asset]:
    assets: dict[str, Asset] = {}
    for spec in catalogue:
        payload_kwargs = dict(
            asset_code=spec["code"], name=spec["name"], asset_type_code=spec["type"],
            department_id=dept.id, administrative_unit_id=spec["unit"].id,
            ownership="Government of Gujarat", address=spec["city"],
            commissioning_date=spec["commissioning"],
            original_cost=spec["cost"],
            current_value=round(spec["cost"] * RNG.uniform(0.35, 0.85), 2),
            useful_life_years=spec["life"],
            expected_end_of_life=(spec["commissioning"] + timedelta(days=spec["life"] * 365)) if spec["commissioning"] else None,
            geometry=spec["geometry"],
            linked_project_id=projects[spec["project_key"]].id if spec.get("project_key") else None,
        )
        payload_kwargs[DETAIL_FIELD[spec["type"]]] = spec["detail"]
        payload = AssetCreate(**payload_kwargs)
        asset = asset_service.create_asset(db, payload, state_admin)
        db.flush()

        advance_to(db, asset, state_admin, spec["lifecycle"])
        if spec["condition"] is not None:
            asset.current_condition = spec["condition"]

        assets[spec["code"]] = asset
    db.commit()
    return assets


# ---------------------------------------------------------------------------
# Inspections, maintenance, grievances, tenders, notifications
# ---------------------------------------------------------------------------

def seed_inspections_and_maintenance(db, assets: dict[str, Asset], users: dict[str, User], contractors: dict[str, Contractor]) -> dict:
    """Returns a dict of created findings/requests keyed by asset code, for
    grievance-to-maintenance linkage below."""

    field_engineer, department_admin, maintenance_officer, state_admin = (
        users["field_engineer"], users["dept_admin"], users["maintenance_officer"], users["state_admin"]
    )

    def add_inspection(asset_code, *, status, overall_condition=None, remarks="", findings=None, reviewed=False, days_ago=5, assigned_ahead=None):
        asset = assets[asset_code]
        insp = Inspection(
            asset_id=asset.id, inspector_id=field_engineer.id,
            assigned_date=date.today() + timedelta(days=assigned_ahead) if assigned_ahead is not None else date.today() - timedelta(days=days_ago + 2),
            inspection_date=None if status == InspectionStatus.ASSIGNED else date.today() - timedelta(days=days_ago),
            overall_condition=overall_condition, remarks=remarks, status=status,
        )
        if reviewed:
            insp.reviewed_by = department_admin.id
            insp.reviewed_at = datetime.now(timezone.utc) - timedelta(days=max(days_ago - 1, 0))
            insp.review_comments = "Reviewed and approved." if status == InspectionStatus.APPROVED else "Returned for clarification."
        db.add(insp)
        db.flush()
        finding_objs = []
        for desc, severity, recommends in (findings or []):
            f = InspectionFinding(inspection_id=insp.id, description=desc, severity=severity, recommends_maintenance=recommends)
            db.add(f)
            db.flush()
            finding_objs.append(f)
        if overall_condition is not None and status != InspectionStatus.ASSIGNED:
            result = compute_condition(asset, insp, open_maintenance_request_count=0, criticality=0.7)
            db.add(ConditionAssessment(asset_id=asset.id, inspection_id=insp.id, assessed_by=field_engineer.id, **result))
        return insp, finding_objs

    _, f_bridge1 = add_inspection("RB-BRIDGE-0001", status=InspectionStatus.APPROVED, overall_condition=ConditionRating.POOR,
        remarks="Visible corrosion on railings; deck surface cracking observed.", reviewed=True, days_ago=8,
        findings=[("Corrosion on span 2 railing", FindingSeverity.MEDIUM, True)])
    _, f_bridge2 = add_inspection("RB-BRIDGE-0002", status=InspectionStatus.SUBMITTED, overall_condition=ConditionRating.CRITICAL,
        remarks="Structural crack observed in main beam; bridge use should be restricted.", days_ago=3,
        findings=[("Structural crack in main beam", FindingSeverity.CRITICAL, True)])
    add_inspection("RB-ROAD-0001", status=InspectionStatus.ASSIGNED, assigned_ahead=3)
    _, f_culvert2 = add_inspection("RB-CULVERT-0002", status=InspectionStatus.APPROVED, overall_condition=ConditionRating.POOR,
        remarks="Silt build-up and a cracked headwall at the outlet.", reviewed=True, days_ago=15,
        findings=[("Cracked headwall at outlet", FindingSeverity.HIGH, True)])
    add_inspection("RB-ROAD-0008", status=InspectionStatus.RETURNED, overall_condition=ConditionRating.POOR,
        remarks="Surface distress along full stretch; needs a fuller condition survey before approval.", reviewed=True, days_ago=12,
        findings=[("Extensive pothole formation", FindingSeverity.HIGH, True)])
    _, f_bedi = add_inspection("RB-CULVERT-0007", status=InspectionStatus.APPROVED, overall_condition=ConditionRating.POOR,
        remarks="Partial blockage from tidal silt deposits near the port.", reviewed=True, days_ago=20,
        findings=[("Tidal silt blocking half the opening", FindingSeverity.MEDIUM, True)])
    add_inspection("RB-BRIDGE-0004", status=InspectionStatus.APPROVED, overall_condition=ConditionRating.FAIR,
        remarks="General wear consistent with age; no urgent action needed.", reviewed=True, days_ago=25)
    add_inspection("RB-ROAD-0007", status=InspectionStatus.ASSIGNED, assigned_ahead=7)
    add_inspection("RB-BRIDGE-0005", status=InspectionStatus.APPROVED, overall_condition=ConditionRating.FAIR,
        remarks="Minor scaling on pier surfaces; monitor at next cycle.", reviewed=True, days_ago=40)
    add_inspection("RB-CULVERT-0004", status=InspectionStatus.APPROVED, overall_condition=ConditionRating.GOOD,
        remarks="No defects observed.", reviewed=True, days_ago=18)

    # ---- Maintenance requests / work orders ----
    def add_request(asset_code, *, mtype, priority, description, status, finding=None, requested_by=None, approved_by=None, days_due=20):
        req = MaintenanceRequest(
            asset_id=assets[asset_code].id, source_inspection_finding_id=finding.id if finding else None,
            maintenance_type=mtype, priority=priority, description=description,
            estimated_cost=RNG.randint(15, 900) * 1000, due_date=date.today() + timedelta(days=days_due),
            status=status, requested_by=(requested_by or field_engineer).id, approved_by=approved_by.id if approved_by else None,
        )
        db.add(req)
        db.flush()
        return req

    def add_work_order(req, *, code, contractor, officer, priority, status, sla_days=14, started=False, completed=False, closed=False, actual_cost=None, remarks=None):
        wo = WorkOrder(
            work_order_code=code, maintenance_request_id=req.id, asset_id=req.asset_id,
            contractor_id=contractor.id if contractor else None, assigned_officer_id=officer.id if officer else None,
            priority=priority, status=status, sla_due_date=date.today() + timedelta(days=sla_days),
            estimated_cost=req.estimated_cost,
        )
        db.add(wo)
        db.flush()
        db.add(MaintenanceRecord(work_order_id=wo.id, event="ASSIGNED", recorded_by=department_admin.id))
        if started:
            db.add(MaintenanceRecord(work_order_id=wo.id, event="STARTED", recorded_by=maintenance_officer.id))
        if completed:
            wo.completed_at = date.today() - timedelta(days=2)
            wo.actual_cost = actual_cost or wo.estimated_cost
            wo.completion_remarks = remarks or "Work completed as scoped."
            db.add(MaintenanceRecord(work_order_id=wo.id, event="COMPLETED", notes=wo.completion_remarks, recorded_by=maintenance_officer.id))
        if closed:
            wo.verified_by = department_admin.id
            wo.verified_at = date.today() - timedelta(days=1)
            db.add(MaintenanceRecord(work_order_id=wo.id, event="VERIFIED", recorded_by=department_admin.id))
        return wo

    req1 = add_request("RB-BRIDGE-0001", mtype=MaintenanceType.CORRECTIVE, priority=MaintenancePriority.HIGH,
        description="Repair corroded railing and seal deck cracks on span 2.", status=MaintenanceRequestStatus.APPROVED,
        finding=f_bridge1[0], approved_by=department_admin, days_due=20)
    add_work_order(req1, code="WO-10000001", contractor=contractors["shree"], officer=maintenance_officer,
        priority=MaintenancePriority.HIGH, status=WorkOrderStatus.IN_PROGRESS, started=True)

    req2 = add_request("RB-BRIDGE-0002", mtype=MaintenanceType.EMERGENCY, priority=MaintenancePriority.URGENT,
        description="Emergency structural repair of main beam crack; consider load restriction.",
        status=MaintenanceRequestStatus.OPEN, finding=f_bridge2[0], days_due=5)

    req3 = add_request("RB-CULVERT-0001", mtype=MaintenanceType.PREVENTIVE, priority=MaintenancePriority.LOW,
        description="Routine desilting of culvert inlet/outlet.", status=MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER,
        requested_by=maintenance_officer, approved_by=department_admin, days_due=-60)
    add_work_order(req3, code="WO-10000002", contractor=contractors["mahalaxmi"], officer=maintenance_officer,
        priority=MaintenancePriority.LOW, status=WorkOrderStatus.CLOSED, started=True, completed=True, closed=True,
        actual_cost=14200, remarks="Desilting completed, inlet/outlet cleared.")

    req4 = add_request("RB-CULVERT-0002", mtype=MaintenanceType.CORRECTIVE, priority=MaintenancePriority.HIGH,
        description="Rebuild cracked headwall at Chandola Lake outfall culvert.", status=MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER,
        finding=f_culvert2[0], approved_by=department_admin, days_due=10)
    add_work_order(req4, code="WO-10000003", contractor=contractors["ghe"], officer=maintenance_officer,
        priority=MaintenancePriority.HIGH, status=WorkOrderStatus.COMPLETED, started=True, completed=True,
        actual_cost=95000, remarks="Headwall rebuilt; awaiting supervisor verification.")

    req5 = add_request("RB-ROAD-0008", mtype=MaintenanceType.CORRECTIVE, priority=MaintenancePriority.MEDIUM,
        description="Pothole patching and resurfacing along Nyari Dam Approach Road.", status=MaintenanceRequestStatus.APPROVED,
        approved_by=department_admin, days_due=25)
    add_work_order(req5, code="WO-10000004", contractor=contractors["sip"], officer=maintenance_officer,
        priority=MaintenancePriority.MEDIUM, status=WorkOrderStatus.ASSIGNED)

    add_request("RB-CULVERT-0007", mtype=MaintenanceType.PREVENTIVE, priority=MaintenancePriority.MEDIUM,
        description="Clear tidal silt from Bedi Port Culvert opening.", status=MaintenanceRequestStatus.OPEN,
        finding=f_bedi[0], days_due=15)

    add_request("RB-BLDG-0005", mtype=MaintenanceType.PREVENTIVE, priority=MaintenancePriority.LOW,
        description="Repaint exterior and service HVAC at Vadodara PWD Office.", status=MaintenanceRequestStatus.REJECTED,
        requested_by=maintenance_officer, days_due=30)

    req8 = add_request("RB-ROAD-0009", mtype=MaintenanceType.CORRECTIVE, priority=MaintenancePriority.MEDIUM,
        description="Shoulder repair and drainage clearing along Bhavnagar Port Road.", status=MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER,
        approved_by=department_admin, days_due=18)
    add_work_order(req8, code="WO-10000005", contractor=contractors["nbw"], officer=maintenance_officer,
        priority=MaintenancePriority.MEDIUM, status=WorkOrderStatus.CREATED)

    return {"req2": req2}


def seed_grievances(db, assets: dict[str, Asset], users: dict[str, User]) -> None:
    field_engineer, department_admin, maintenance_officer = users["field_engineer"], users["dept_admin"], users["maintenance_officer"]

    entries = [
        dict(code="GRV-00000001", title="Tree root water seepage cracking asphalt near KM 3",
             description="A large roadside tree's roots have lifted the asphalt near KM 3 of SH-12, and water "
                          "seeping from the root zone after rain is softening the base, causing the surface to crack "
                          "and a pothole to form. Needs patch repair and root/drainage management.",
             category=GrievanceCategory.TREE_HAZARD, severity=FindingSeverity.MEDIUM, status=GrievanceStatus.ACKNOWLEDGED,
             asset="RB-ROAD-0001", offset=(-0.02, 0.01), reporter="Local Resident", contact="9812345670", assigned=maintenance_officer),
        dict(code="GRV-00000002", title="Railing corrosion visible from footpath",
             description="Passersby have noticed rust and a loose railing section on the Sabarmati River Bridge, span 2.",
             category=GrievanceCategory.STRUCTURAL_DAMAGE, severity=FindingSeverity.MEDIUM, status=GrievanceStatus.RESOLVED,
             asset="RB-BRIDGE-0001", offset=(0, 0), reporter="Anonymous", resolved=True,
             resolution="Linked to existing corrective work order; railing repair completed."),
        dict(code="GRV-00000003", title="Water logging at culvert outlet after rain",
             description="Persistent water logging observed at the Sabarmati Canal Culvert outlet, likely due to silt blockage.",
             category=GrievanceCategory.WATER_LOGGING, severity=FindingSeverity.LOW, status=GrievanceStatus.OPEN,
             asset="RB-CULVERT-0001", offset=(0, 0), reporter="Farmer nearby", contact="9876500001"),
        dict(code="GRV-00000004", title="Deep crack near bridge expansion joint",
             description="A growing structural crack was spotted near the main beam / expansion joint — flagged as urgent.",
             category=GrievanceCategory.STRUCTURAL_DAMAGE, severity=FindingSeverity.CRITICAL, status=GrievanceStatus.IN_PROGRESS,
             asset="RB-BRIDGE-0002", offset=(0, 0), reporter="Site Inspector", assigned=field_engineer),
        dict(code="GRV-00000005", title="Pothole cluster near Surat bypass toll plaza",
             description="Multiple potholes have formed near the toll plaza approach, causing traffic to swerve dangerously.",
             category=GrievanceCategory.POTHOLE, severity=FindingSeverity.HIGH, status=GrievanceStatus.OPEN,
             asset="RB-ROAD-0004", offset=(0.01, -0.005), reporter="Truck Driver Association", contact="9900011122"),
        dict(code="GRV-00000006", title="Streetlight and railing missing on Tapi bridge footpath",
             description="Several footpath railing sections and a streetlight pole are missing near mid-span.",
             category=GrievanceCategory.SAFETY_HAZARD, severity=FindingSeverity.MEDIUM, status=GrievanceStatus.ACKNOWLEDGED,
             asset="RB-BRIDGE-0004", offset=(0, 0.001), reporter="Evening Walker", contact="9822233344", assigned=field_engineer),
        dict(code="GRV-00000007", title="Encroachment narrowing Ajwa Road culvert drain",
             description="A roadside vendor stall has been built partially over the culvert drain, restricting water flow.",
             category=GrievanceCategory.ENCROACHMENT, severity=FindingSeverity.MEDIUM, status=GrievanceStatus.OPEN,
             asset="RB-CULVERT-0004", offset=(0, 0), reporter="Nearby Shopkeeper"),
        dict(code="GRV-00000008", title="Exposed electrical wiring at Rajkot rest house",
             description="Exposed and frayed wiring was noticed near the rest house entrance porch — safety risk.",
             category=GrievanceCategory.ELECTRICAL_HAZARD, severity=FindingSeverity.HIGH, status=GrievanceStatus.RESOLVED,
             asset="RB-BLDG-0002", offset=(0, 0), reporter="Visiting Officer", resolved=True,
             resolution="Wiring inspected and replaced by electrical contractor."),
        dict(code="GRV-00000009", title="Large pothole formed after monsoon near Nyari Dam road",
             description="A large, deep pothole has formed roughly 2km from the dam gate, already causing a two-wheeler accident.",
             category=GrievanceCategory.POTHOLE, severity=FindingSeverity.HIGH, status=GrievanceStatus.IN_PROGRESS,
             asset="RB-ROAD-0008", offset=(0.005, 0.01), reporter="Local Panchayat", contact="9765432109", assigned=maintenance_officer),
        dict(code="GRV-00000010", title="Silt blocking half the Bedi Port culvert opening",
             description="Tidal silt has built up and now blocks roughly half the culvert opening, worsening local flooding at high tide.",
             category=GrievanceCategory.WATER_LOGGING, severity=FindingSeverity.MEDIUM, status=GrievanceStatus.OPEN,
             asset="RB-CULVERT-0007", offset=(0, 0), reporter="Port Authority Staff"),
        dict(code="GRV-00000011", title="Cracked boundary wall at Bhavnagar guest house",
             description="A section of the compound boundary wall has developed a wide crack and is leaning slightly.",
             category=GrievanceCategory.STRUCTURAL_DAMAGE, severity=FindingSeverity.LOW, status=GrievanceStatus.REJECTED,
             asset="RB-BLDG-0006", offset=(0, 0), reporter="Caretaker",
             resolved=True, resolution="Inspected — cosmetic settlement crack, not structural. No action needed."),
        dict(code="GRV-00000012", title="Median trees leaning onto refinery road carriageway",
             description="Several median trees are leaning over after recent winds, with low branches now obstructing tall vehicles.",
             category=GrievanceCategory.TREE_HAZARD, severity=FindingSeverity.MEDIUM, status=GrievanceStatus.OPEN,
             asset="RB-ROAD-0010", offset=(-0.01, 0.02), reporter="Transport Company", contact="9988776655"),
    ]

    for e in entries:
        asset = assets.get(e["asset"])
        base = asset_service.serialize_asset(db, asset)["geometry"] if asset else None
        if base and base["type"] == "Point":
            lon, lat = base["coordinates"]
        elif base and base["type"] == "LineString":
            lon, lat = base["coordinates"][0]
        elif base and base["type"] == "Polygon":
            lon, lat = base["coordinates"][0][0]
        else:
            lon, lat = CITIES["ahmedabad"]["center"]
        dx, dy = e.get("offset", (0, 0))
        g = Grievance(
            grievance_code=e["code"], title=e["title"], description=e["description"],
            category=e["category"], severity=e["severity"], status=e["status"],
            location={"type": "Point", "coordinates": [lon + dx, lat + dy]}, asset_id=asset.id if asset else None,
            reporter_name=e.get("reporter"), reporter_contact=e.get("contact"),
            assigned_to=e["assigned"].id if e.get("assigned") else None,
        )
        if e.get("resolved"):
            g.resolved_by = department_admin.id
            g.resolved_at = datetime.now(timezone.utc) - timedelta(days=RNG.randint(1, 10))
            g.resolution_notes = e.get("resolution")
        db.add(g)


def seed_tenders(db, dept: Department, units: dict, assets: dict[str, Asset], projects: dict[str, Project],
                  contractors: dict[str, Contractor], state_admin: User) -> None:
    entries = [
        dict(number="GEM/2026/RB/000101", title="Emergency structural repair — Aji River Bridge",
             description="Urgent repair of the main beam crack and load-capacity restoration for the Aji River Bridge.",
             asset="RB-BRIDGE-0002", unit=units["rajkot"]["division"], status=TenderStatus.AWARDED,
             value=900_000, emd=45_000, published_days_ago=30, deadline_days_ago=15,
             bids=[("shree", 870_000, TenderBidStatus.AWARDED, "6-week completion, includes load testing."),
                   ("mahalaxmi", 910_000, TenderBidStatus.REJECTED, "8-week completion.")],
             award_days_ago=10),
        dict(number="GEM/2026/RB/000102", title="Resurfacing — SH-12 Ahmedabad Bypass (KM 0-12)",
             description="Full-length resurfacing and pothole rectification for SH-12, including drainage improvements near KM 3.",
             asset="RB-ROAD-0001", unit=units["ahmedabad"]["division"], status=TenderStatus.PUBLISHED,
             value=4_800_000, emd=150_000, published_days_ago=5, deadline_days_ahead=10,
             # Deliberately NOT "shree" — that contractor is linked to the demo
             # contractor.user@rnb.gov.in login, and this is the only tender left
             # open for bidding. Pre-seeding a bid from that same contractor here
             # would make every demo login immediately hit "already bid" (409).
             bids=[("mahalaxmi", 4_650_000, TenderBidStatus.SUBMITTED, "Includes drainage rework near KM 3.")]),
        dict(number="GEM/2026/RB/000103", title="Annual desilting — Sabarmati Canal Culvert",
             description="Routine annual desilting and inlet/outlet clearance contract.",
             asset="RB-CULVERT-0001", unit=units["ahmedabad"]["division"], status=TenderStatus.DRAFT,
             value=60_000),
        dict(number="GEM/2026/RB/000104", title="Surat Ring Road Phase 2 — Civil Works",
             description="Construction of the Phase 2 stretch of Surat Ring Road, 9.2 km, 4-lane divided carriageway.",
             asset="RB-ROAD-0005", project="surat_ring_road", unit=units["surat"]["division"], status=TenderStatus.AWARDED,
             value=21_000_000, emd=600_000, published_days_ago=180, deadline_days_ago=140,
             bids=[("ghe", 20_100_000, TenderBidStatus.AWARDED, "18-month completion timeline."),
                   ("sip", 20_800_000, TenderBidStatus.REJECTED, "20-month completion timeline."),
                   ("nbw", 21_400_000, TenderBidStatus.REJECTED, "22-month completion timeline.")],
             award_days_ago=120),
        dict(number="GEM/2026/RB/000105", title="Vadodara-Halol Expressway Link — Earthwork & Paving",
             description="Earthwork, sub-base and bituminous paving for the Vadodara-Halol expressway link road.",
             asset="RB-ROAD-0006", project="vadodara_expressway", unit=units["vadodara"]["division"], status=TenderStatus.AWARDED,
             value=34_000_000, emd=900_000, published_days_ago=220, deadline_days_ago=190,
             bids=[("nbw", 32_800_000, TenderBidStatus.AWARDED, "Phased handover by section."),
                   ("shree", 33_500_000, TenderBidStatus.REJECTED, "Single handover at completion.")],
             award_days_ago=170),
        dict(number="GEM/2026/RB/000106", title="Headwall reconstruction — Chandola Lake Outfall Culvert",
             description="Reconstruction of the cracked headwall and minor desilting at the Chandola Lake outfall culvert.",
             asset="RB-CULVERT-0002", unit=units["ahmedabad"]["division"], status=TenderStatus.BIDDING_CLOSED,
             value=110_000, emd=8_000, published_days_ago=20, deadline_days_ago=3,
             bids=[("ghe", 95_000, TenderBidStatus.SUBMITTED, "2-week completion."),
                   ("mahalaxmi", 105_000, TenderBidStatus.SUBMITTED, "3-week completion.")]),
        dict(number="GEM/2026/RB/000107", title="Bhavnagar Port Road — Shoulder & Drainage Repair",
             description="Shoulder repair and drainage clearing along Bhavnagar Port Road to reduce monsoon flooding.",
             asset="RB-ROAD-0009", unit=units["bhavnagar"]["division"], status=TenderStatus.CANCELLED,
             value=1_200_000, emd=40_000, published_days_ago=60, deadline_days_ago=45,
             bids=[("sip", 1_150_000, TenderBidStatus.REJECTED, "Withdrawn — scope superseded by direct work order.")]),
    ]

    for e in entries:
        asset = assets.get(e.get("asset"))
        t = Tender(
            tender_number=e["number"], title=e["title"], description=e["description"],
            status=e["status"], asset_id=asset.id if asset else None,
            project_id=projects[e["project"]].id if e.get("project") else None,
            department_id=dept.id, administrative_unit_id=e["unit"].id,
            estimated_value=e.get("value"), emd_amount=e.get("emd"),
            published_date=(date.today() - timedelta(days=e["published_days_ago"])) if e.get("published_days_ago") else None,
            submission_deadline=(date.today() - timedelta(days=e["deadline_days_ago"])) if e.get("deadline_days_ago")
                else (date.today() + timedelta(days=e["deadline_days_ahead"])) if e.get("deadline_days_ahead") else None,
            awarded_at=(datetime.now(timezone.utc) - timedelta(days=e["award_days_ago"])) if e.get("award_days_ago") else None,
            created_by=state_admin.id,
        )
        db.add(t)
        db.flush()
        awarded_bid_id = None
        for contractor_key, amount, bid_status, remarks in e.get("bids", []):
            bid = TenderBid(tender_id=t.id, contractor_id=contractors[contractor_key].id, bid_amount=amount, status=bid_status, remarks=remarks)
            db.add(bid)
            db.flush()
            if bid_status == TenderBidStatus.AWARDED:
                awarded_bid_id = bid.id
        if awarded_bid_id:
            t.awarded_bid_id = awarded_bid_id


def seed_notifications(db, users: dict[str, User], assets: dict[str, Asset], reqs: dict) -> None:
    db.add(Notification(
        recipient_id=users["dept_admin"].id, event=NotificationEvent.APPROVAL_PENDING,
        title="Maintenance request pending approval", body="Emergency repair request for Aji River Bridge needs your decision.",
        context={"maintenance_request_id": str(reqs["req2"].id)},
    ))
    db.add(Notification(
        recipient_id=users["state_admin"].id, event=NotificationEvent.CRITICAL_CONDITION,
        title="Critical asset condition", body="Aji River Bridge assessed as CRITICAL after inspection.",
        context={"asset_id": str(assets["RB-BRIDGE-0002"].id)},
    ))
    db.add(Notification(
        recipient_id=users["maintenance_officer"].id, event=NotificationEvent.MAINTENANCE_DUE,
        title="Work order SLA approaching", body="WO-10000004 (Nyari Dam Approach Road) is due soon.",
        context={"work_order_code": "WO-10000004"},
    ))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run():
    db = SessionLocal()
    try:
        dept = upsert_department(db)
        units = build_admin_hierarchy(db)
        roles = upsert_roles(db)

        state_admin = upsert_user(db, "state.admin@rnb.gov.in", "Asha Rao (State Admin)", dept, units["state"], [roles[SystemRole.STATE_ADMIN.value]])
        dept_admin = upsert_user(db, "dept.admin@rnb.gov.in", "Vikram Shah (Dept Admin)", dept, units["state"], [roles[SystemRole.DEPARTMENT_ADMIN.value]])
        field_engineer = upsert_user(db, "field.engineer@rnb.gov.in", "Priya Deshmukh (Field Engineer)", dept, units["ahmedabad"]["sub_division"], [roles[SystemRole.FIELD_ENGINEER.value]])
        maintenance_officer = upsert_user(db, "maintenance.officer@rnb.gov.in", "Sanjay More (Maintenance Officer)", dept, units["ahmedabad"]["sub_division"], [roles[SystemRole.MAINTENANCE_OFFICER.value]])
        contractor_user = upsert_user(db, "contractor.user@rnb.gov.in", "Amit Verma (Contractor)", None, None, [roles[SystemRole.CONTRACTOR.value]])

        for retired_email in ("circle.north@rnb.gov.in", "subdivision.n1a@rnb.gov.in", "auditor@rnb.gov.in"):
            retired_user = db.query(User).filter(User.email == retired_email).first()
            if retired_user:
                retired_user.is_active = False
        db.flush()

        users = {
            "state_admin": state_admin, "dept_admin": dept_admin, "circle_officer": dept_admin,
            "subdivision_officer": dept_admin, "field_engineer": field_engineer,
            "maintenance_officer": maintenance_officer, "contractor_user": contractor_user,
        }

        category = upsert_asset_category(db)
        upsert_asset_types(db, category)

        contractors = {
            "shree": upsert_contractor(db, "Shree Constructions Pvt Ltd", "REG-SHREE-001", "Bharat Shah", "9825011001"),
            "mahalaxmi": upsert_contractor(db, "Mahalaxmi Infra Builders", "REG-MAHA-002", "Kiran Mehta", "9825011002"),
            "ghe": upsert_contractor(db, "Gujarat Highway Engineers Pvt Ltd", "REG-GHE-003", "Rajesh Trivedi", "9825011003"),
            "sip": upsert_contractor(db, "Saurashtra Infra Projects", "REG-SIP-004", "Devang Vora", "9825011004"),
            "nbw": upsert_contractor(db, "Narmada Bridge Works LLP", "REG-NBW-005", "Alpesh Patel", "9825011005"),
        }
        if not contractors["shree"].user_id:
            contractors["shree"].user_id = contractor_user.id

        # Business data is regenerated fresh each run for internal consistency.
        clear_business_data(db)

        projects = {}
        # completion_offset_days: signed days from today to expected completion
        # (positive = future / still on track, negative = was due in the past).
        project_specs = [
            ("ahmedabad_connector", "PRJ-0001", "Ahmedabad-Sabarmati Connector Phase 1",
             "Widening of the Sabarmati riverfront connector to 4 lanes.", ProjectStatus.IN_PROGRESS,
             units["ahmedabad"]["sub_division"], contractors["shree"], 45_000_000, 18_000_000, 200, 150, 120, None),
            ("rajkot_rehab", "PRJ-0002", "Rajkot Bridge Rehabilitation",
             "Rehabilitation of the ageing Aji River timber bridge structure.", ProjectStatus.COMPLETED,
             units["rajkot"]["sub_division"], contractors["mahalaxmi"], 12_000_000, 11_500_000, 500, 460, -100, 95),
            ("surat_ring_road", "PRJ-0003", "Surat Ring Road Expansion",
             "Phase 2 construction of the Surat Ring Road, adding 9.2 km of 4-lane carriageway.", ProjectStatus.IN_PROGRESS,
             units["surat"]["division"], contractors["ghe"], 21_000_000, 6_500_000, 180, 140, 300, None),
            ("vadodara_expressway", "PRJ-0004", "Vadodara-Halol Expressway Link",
             "New expressway link road connecting Vadodara to the Halol industrial corridor.", ProjectStatus.IN_PROGRESS,
             units["vadodara"]["sub_division"], contractors["nbw"], 34_000_000, 9_000_000, 220, 190, 260, None),
            ("bhavnagar_port", "PRJ-0005", "Bhavnagar Port Connectivity Upgrade",
             "Sanctioned upgrade of port-connecting road infrastructure around Bhavnagar.", ProjectStatus.SANCTIONED,
             units["bhavnagar"]["division"], contractors["sip"], 8_500_000, None, 40, None, 400, None),
        ]
        for key, code, name, desc, status, unit, contractor, budget, expenditure, sanction_days, start_days, completion_offset_days, actual_completion_days in project_specs:
            p = Project(
                project_code=code, name=name, description=desc, status=status,
                department_id=dept.id, administrative_unit_id=unit.id,
                sanctioned_budget=budget, actual_expenditure=expenditure,
                sanction_date=date.today() - timedelta(days=sanction_days) if sanction_days else None,
                start_date=date.today() - timedelta(days=start_days) if start_days else None,
                expected_completion_date=date.today() + timedelta(days=completion_offset_days) if completion_offset_days is not None else None,
                actual_completion_date=date.today() - timedelta(days=actual_completion_days) if actual_completion_days else None,
                contractor_id=contractor.id, created_by=state_admin.id,
            )
            db.add(p)
            db.flush()
            projects[key] = p
        db.commit()

        catalogue = build_asset_catalogue(units)
        assets = create_assets(db, dept, catalogue, state_admin, projects)

        for key, code in [("ahmedabad_connector", "RB-ROAD-0002"), ("surat_ring_road", "RB-ROAD-0005"), ("vadodara_expressway", "RB-ROAD-0006")]:
            db.add(ProjectAsset(project_id=projects[key].id, asset_id=assets[code].id))
        db.commit()

        maintenance_refs = seed_inspections_and_maintenance(db, assets, users, contractors)
        db.commit()

        seed_grievances(db, assets, users)
        db.commit()

        seed_tenders(db, dept, units, assets, projects, contractors, state_admin)
        db.commit()

        seed_notifications(db, users, assets, maintenance_refs)
        db.commit()

        print(f"Seed data created successfully — {len(assets)} assets across {len(CITIES)} cities.")
        print_credentials()
    finally:
        db.close()


def print_credentials():
    print("\nDemo login credentials (password for all): " + DEMO_PASSWORD)
    for email, role in [
        ("state.admin@rnb.gov.in", "State Admin"),
        ("dept.admin@rnb.gov.in", "Department Admin"),
        ("field.engineer@rnb.gov.in", "Field Engineer / Inspector"),
        ("maintenance.officer@rnb.gov.in", "Maintenance Officer"),
        ("contractor.user@rnb.gov.in", "Contractor"),
    ]:
        print(f"  {email:35s} {role}")


if __name__ == "__main__":
    run()
