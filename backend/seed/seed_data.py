"""Synthetic demo data for the hackathon presentation. None of this represents
real government records. Run with:

    cd backend
    python -m seed.seed_data
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
    InspectionStatus,
    LifecycleStatus,
    MaintenancePriority,
    MaintenanceRequestStatus,
    MaintenanceType,
    NotificationEvent,
    ProjectStatus,
    SystemRole,
    WorkOrderStatus,
)
from app.models.geo import AdministrativeUnit, Department
from app.models.inspection import Inspection, InspectionFinding
from app.models.maintenance import MaintenanceRecord, MaintenanceRequest, WorkOrder
from app.models.notification import Notification
from app.models.project import Project, ProjectAsset
from app.models.user import Role, User, UserRole
from app.schemas.asset import AssetCreate, BridgeDetail, BuildingDetail, CulvertDetail, RoadDetail, StructureDetail
from app.services import asset_service
from app.services.condition_service import compute_condition
from app.services.lifecycle_service import transition_asset

DEMO_PASSWORD = "Password123!"


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


def upsert_contractor(db, name, reg_no) -> Contractor:
    existing = db.query(Contractor).filter(Contractor.registration_number == reg_no).first()
    if existing:
        return existing
    c = Contractor(name=name, registration_number=reg_no, contact_person="Site Manager", phone="9800000000", email=f"{reg_no.lower()}@example.com")
    db.add(c)
    db.flush()
    return c


def run():
    db = SessionLocal()
    try:
        dept = upsert_department(db)

        state = upsert_admin_unit(db, "ST", "State of Pravinagar", AdminUnitLevel.STATE, None)
        circle_n = upsert_admin_unit(db, "CIR-N", "Northern Circle", AdminUnitLevel.REGION_CIRCLE, state)
        div_n1 = upsert_admin_unit(db, "DIV-N1", "Northern Division 1", AdminUnitLevel.DIVISION, circle_n)
        sd_n1a = upsert_admin_unit(db, "SD-N1A", "Sub-Division N1-A", AdminUnitLevel.SUB_DIVISION, div_n1)
        sec_n1a1 = upsert_admin_unit(db, "SEC-N1A1", "Field Section N1-A1", AdminUnitLevel.SECTION_FIELD_OFFICE, sd_n1a)

        circle_s = upsert_admin_unit(db, "CIR-S", "Southern Circle", AdminUnitLevel.REGION_CIRCLE, state)
        div_s1 = upsert_admin_unit(db, "DIV-S1", "Southern Division 1", AdminUnitLevel.DIVISION, circle_s)
        sd_s1a = upsert_admin_unit(db, "SD-S1A", "Sub-Division S1-A", AdminUnitLevel.SUB_DIVISION, div_s1)

        roles = upsert_roles(db)

        state_admin = upsert_user(db, "state.admin@rnb.gov.in", "Asha Rao (State Admin)", dept, state, [roles[SystemRole.STATE_ADMIN.value]])
        dept_admin = upsert_user(db, "dept.admin@rnb.gov.in", "Vikram Shah (Dept Admin)", dept, state, [roles[SystemRole.DEPARTMENT_ADMIN.value]])
        circle_officer = upsert_user(db, "circle.north@rnb.gov.in", "Neha Kulkarni (Circle Officer)", dept, circle_n, [roles[SystemRole.CIRCLE_DIVISION_OFFICER.value]])
        subdivision_officer = upsert_user(db, "subdivision.n1a@rnb.gov.in", "Ramesh Patil (Sub-Division Officer)", dept, sd_n1a, [roles[SystemRole.SUB_DIVISION_OFFICER.value]])
        field_engineer = upsert_user(db, "field.engineer@rnb.gov.in", "Priya Deshmukh (Field Engineer)", dept, sd_n1a, [roles[SystemRole.FIELD_ENGINEER.value]])
        maintenance_officer = upsert_user(db, "maintenance.officer@rnb.gov.in", "Sanjay More (Maintenance Officer)", dept, sd_n1a, [roles[SystemRole.MAINTENANCE_OFFICER.value]])
        auditor = upsert_user(db, "auditor@rnb.gov.in", "Kavita Joshi (Auditor)", dept, state, [roles[SystemRole.AUDITOR.value]])
        contractor_user = upsert_user(db, "contractor.user@rnb.gov.in", "Amit Verma (Contractor)", None, None, [roles[SystemRole.CONTRACTOR.value]])
        db.flush()

        category = upsert_asset_category(db)
        asset_types = upsert_asset_types(db, category)

        contractor1 = upsert_contractor(db, "Shree Constructions Pvt Ltd", "REG-SHREE-001")
        contractor2 = upsert_contractor(db, "Mahalaxmi Infra Builders", "REG-MAHA-002")
        if not contractor1.user_id:
            contractor1.user_id = contractor_user.id

        project1 = db.query(Project).filter(Project.project_code == "PRJ-0001").first()
        if not project1:
            project1 = Project(
                project_code="PRJ-0001", name="NH-Link Road Widening Phase 1", description="Widening of the coastal link road to 4 lanes.",
                status=ProjectStatus.IN_PROGRESS, department_id=dept.id, administrative_unit_id=sd_n1a.id,
                sanctioned_budget=45000000, actual_expenditure=18000000,
                sanction_date=date.today() - timedelta(days=200), start_date=date.today() - timedelta(days=150),
                expected_completion_date=date.today() + timedelta(days=120),
                contractor_id=contractor1.id, created_by=state_admin.id,
            )
            db.add(project1)
            db.flush()

        project2 = db.query(Project).filter(Project.project_code == "PRJ-0002").first()
        if not project2:
            project2 = Project(
                project_code="PRJ-0002", name="District Bridge Rehabilitation", description="Rehabilitation of ageing timber bridges.",
                status=ProjectStatus.COMPLETED, department_id=dept.id, administrative_unit_id=sd_s1a.id,
                sanctioned_budget=12000000, actual_expenditure=11500000,
                sanction_date=date.today() - timedelta(days=500), start_date=date.today() - timedelta(days=460),
                expected_completion_date=date.today() - timedelta(days=100), actual_completion_date=date.today() - timedelta(days=95),
                contractor_id=contractor2.id, created_by=state_admin.id,
            )
            db.add(project2)
            db.flush()

        if db.query(Asset).count() > 0:
            print("Assets already seeded, skipping asset creation.")
            db.commit()
            print_credentials()
            return

        def make_asset(**kwargs) -> Asset:
            payload = AssetCreate(**kwargs)
            return asset_service.create_asset(db, payload, state_admin)

        road1 = make_asset(
            asset_code="RB-ROAD-0001", name="SH-12 Northern Bypass", asset_type_code=AssetTypeCode.ROAD,
            department_id=dept.id, administrative_unit_id=sd_n1a.id, ownership="Government of Pravinagar",
            commissioning_date=date(2015, 6, 1), original_cost=8000000, current_value=5200000, useful_life_years=25,
            expected_end_of_life=date(2040, 6, 1),
            geometry={"type": "LineString", "coordinates": [[73.85, 18.52], [73.90, 18.55], [73.95, 18.58]]},
            road=RoadDetail(length_km=12.4, width_m=7.0, number_of_lanes=2, surface_type="Bituminous", start_point_desc="Junction KM 0", end_point_desc="Northern Toll Plaza"),
        )
        road2 = make_asset(
            asset_code="RB-ROAD-0002", name="Coastal Link Road", asset_type_code=AssetTypeCode.ROAD,
            department_id=dept.id, administrative_unit_id=sd_n1a.id, ownership="Government of Pravinagar",
            linked_project_id=project1.id,
            geometry={"type": "LineString", "coordinates": [[73.80, 18.48], [73.83, 18.50]]},
            road=RoadDetail(length_km=6.1, width_m=10.0, number_of_lanes=4, surface_type="Bituminous (under widening)"),
        )
        db.flush()
        transition_asset(db, road2, LifecycleStatus.SANCTIONED, state_admin, "Seed: project sanctioned")
        transition_asset(db, road2, LifecycleStatus.UNDER_CONSTRUCTION, state_admin, "Seed: widening works in progress")
        db.add(ProjectAsset(project_id=project1.id, asset_id=road2.id))

        bridge1 = make_asset(
            asset_code="RB-BRIDGE-0001", name="Kaveri River Bridge", asset_type_code=AssetTypeCode.BRIDGE,
            department_id=dept.id, administrative_unit_id=sd_n1a.id, ownership="Government of Pravinagar",
            commissioning_date=date(2005, 3, 1), original_cost=15000000, current_value=6000000, useful_life_years=30,
            expected_end_of_life=date(2035, 3, 1),
            geometry={"type": "Point", "coordinates": [73.91, 18.56]},
            bridge=BridgeDetail(length_m=180, width_m=9, number_of_spans=3, bridge_type="Girder", material="RCC", load_capacity_tonnes=40),
        )
        bridge2 = make_asset(
            asset_code="RB-BRIDGE-0002", name="Old Timber Bridge", asset_type_code=AssetTypeCode.BRIDGE,
            department_id=dept.id, administrative_unit_id=sd_s1a.id, ownership="Government of Pravinagar",
            commissioning_date=date(1985, 1, 1), original_cost=2000000, current_value=200000, useful_life_years=35,
            expected_end_of_life=date(2020, 1, 1),
            geometry={"type": "Point", "coordinates": [73.75, 18.40]},
            bridge=BridgeDetail(length_m=45, width_m=4, number_of_spans=2, bridge_type="Timber Truss", material="Timber", load_capacity_tonnes=8),
        )

        culvert1 = make_asset(
            asset_code="RB-CULVERT-0001", name="Minor Culvert KM 4.2", asset_type_code=AssetTypeCode.CULVERT,
            department_id=dept.id, administrative_unit_id=sd_n1a.id,
            commissioning_date=date(2012, 1, 1), original_cost=400000, current_value=250000, useful_life_years=20,
            geometry={"type": "Point", "coordinates": [73.88, 18.53]},
            culvert=CulvertDetail(culvert_type="Box Culvert", length_m=6, opening_width_m=2.5, material="RCC"),
        )

        building1 = make_asset(
            asset_code="RB-BLDG-0001", name="Divisional Office Building N1", asset_type_code=AssetTypeCode.BUILDING,
            department_id=dept.id, administrative_unit_id=div_n1.id, ownership="Government of Pravinagar",
            commissioning_date=date(1998, 4, 1), original_cost=3500000, current_value=1800000, useful_life_years=50,
            geometry={"type": "Polygon", "coordinates": [[[73.86, 18.54], [73.862, 18.54], [73.862, 18.542], [73.86, 18.542], [73.86, 18.54]]]},
            building=BuildingDetail(plot_area_sqm=1200, built_up_area_sqm=650, number_of_floors=2, construction_year=1998, building_type="Office", occupancy_use="Divisional administrative office"),
        )
        building2 = make_asset(
            asset_code="RB-BLDG-0002", name="Rest House SD-N1A", asset_type_code=AssetTypeCode.BUILDING,
            department_id=dept.id, administrative_unit_id=sd_n1a.id,
            commissioning_date=date(2010, 8, 1), original_cost=900000, current_value=600000, useful_life_years=40,
            geometry={"type": "Polygon", "coordinates": [[[73.89, 18.51], [73.891, 18.51], [73.891, 18.511], [73.89, 18.511], [73.89, 18.51]]]},
            building=BuildingDetail(plot_area_sqm=400, built_up_area_sqm=180, number_of_floors=1, construction_year=2010, building_type="Rest House", occupancy_use="Field staff accommodation"),
        )

        structure1 = make_asset(
            asset_code="RB-STRUCT-0001", name="Traffic Circle Monument", asset_type_code=AssetTypeCode.PUBLIC_STRUCTURE,
            department_id=dept.id, administrative_unit_id=div_n1.id,
            geometry={"type": "Point", "coordinates": [73.87, 18.545]},
            structure=StructureDetail(structure_subtype="Monument", attributes={"height_m": 6}),
        )

        db.commit()

        # --- Inspections & condition assessments ---
        insp1 = Inspection(
            asset_id=bridge1.id, inspector_id=field_engineer.id, assigned_date=date.today() - timedelta(days=10),
            inspection_date=date.today() - timedelta(days=8), overall_condition=ConditionRating.POOR,
            remarks="Visible corrosion on railings; deck surface cracking observed.",
            status=InspectionStatus.APPROVED, reviewed_by=circle_officer.id, reviewed_at=None, review_comments="Approved, raise corrective maintenance request.",
        )
        db.add(insp1)
        db.flush()
        finding1 = InspectionFinding(inspection_id=insp1.id, description="Corrosion on span 2 railing", severity=FindingSeverity.MEDIUM, recommends_maintenance=True)
        db.add(finding1)
        db.flush()
        result1 = compute_condition(bridge1, insp1, open_maintenance_request_count=0, criticality=0.7)
        db.add(ConditionAssessment(asset_id=bridge1.id, inspection_id=insp1.id, assessed_by=field_engineer.id, **result1))
        bridge1.current_condition = result1["condition_rating"]

        insp2 = Inspection(
            asset_id=bridge2.id, inspector_id=field_engineer.id, assigned_date=date.today() - timedelta(days=5),
            inspection_date=date.today() - timedelta(days=3), overall_condition=ConditionRating.CRITICAL,
            remarks="Structural crack observed in main beam; bridge use should be restricted.",
            status=InspectionStatus.SUBMITTED,
        )
        db.add(insp2)
        db.flush()
        finding2 = InspectionFinding(inspection_id=insp2.id, description="Structural crack in main beam", severity=FindingSeverity.CRITICAL, recommends_maintenance=True)
        db.add(finding2)
        db.flush()
        result2 = compute_condition(bridge2, insp2, open_maintenance_request_count=0, criticality=0.9)
        db.add(ConditionAssessment(asset_id=bridge2.id, inspection_id=insp2.id, assessed_by=field_engineer.id, **result2))
        bridge2.current_condition = result2["condition_rating"]

        insp3 = Inspection(
            asset_id=road1.id, inspector_id=field_engineer.id, assigned_date=date.today() + timedelta(days=3),
            status=InspectionStatus.ASSIGNED,
        )
        db.add(insp3)

        db.commit()

        # --- Maintenance: request -> approved -> work order in progress (bridge1) ---
        req1 = MaintenanceRequest(
            asset_id=bridge1.id, source_inspection_finding_id=finding1.id, maintenance_type=MaintenanceType.CORRECTIVE,
            priority=MaintenancePriority.HIGH, description="Repair corroded railing and seal deck cracks on span 2.",
            estimated_cost=250000, due_date=date.today() + timedelta(days=20),
            status=MaintenanceRequestStatus.APPROVED, requested_by=field_engineer.id, approved_by=circle_officer.id,
        )
        db.add(req1)
        db.flush()
        wo1 = WorkOrder(
            work_order_code="WO-10000001", maintenance_request_id=req1.id, asset_id=bridge1.id,
            contractor_id=contractor1.id, assigned_officer_id=maintenance_officer.id,
            priority=MaintenancePriority.HIGH, status=WorkOrderStatus.IN_PROGRESS,
            sla_due_date=date.today() + timedelta(days=14), estimated_cost=250000,
        )
        db.add(wo1)
        db.flush()
        db.add(MaintenanceRecord(work_order_id=wo1.id, event="ASSIGNED", recorded_by=circle_officer.id))
        db.add(MaintenanceRecord(work_order_id=wo1.id, event="STARTED", recorded_by=maintenance_officer.id))

        # --- Maintenance: request pending decision (bridge2, urgent) ---
        req2 = MaintenanceRequest(
            asset_id=bridge2.id, source_inspection_finding_id=finding2.id, maintenance_type=MaintenanceType.EMERGENCY,
            priority=MaintenancePriority.URGENT, description="Emergency structural repair of main beam crack; consider load restriction.",
            estimated_cost=800000, due_date=date.today() + timedelta(days=5),
            status=MaintenanceRequestStatus.OPEN, requested_by=field_engineer.id,
        )
        db.add(req2)
        db.flush()

        # --- Maintenance: fully closed example (culvert) ---
        req3 = MaintenanceRequest(
            asset_id=culvert1.id, maintenance_type=MaintenanceType.PREVENTIVE, priority=MaintenancePriority.LOW,
            description="Routine desilting of culvert inlet/outlet.", estimated_cost=15000,
            due_date=date.today() - timedelta(days=60), status=MaintenanceRequestStatus.CONVERTED_TO_WORK_ORDER,
            requested_by=maintenance_officer.id, approved_by=circle_officer.id,
        )
        db.add(req3)
        db.flush()
        wo3 = WorkOrder(
            work_order_code="WO-10000002", maintenance_request_id=req3.id, asset_id=culvert1.id,
            contractor_id=contractor2.id, assigned_officer_id=maintenance_officer.id,
            priority=MaintenancePriority.LOW, status=WorkOrderStatus.CLOSED,
            sla_due_date=date.today() - timedelta(days=55), estimated_cost=15000, actual_cost=14200,
            completed_at=date.today() - timedelta(days=56), completion_remarks="Desilting completed, inlet/outlet cleared.",
            verified_by=circle_officer.id, verified_at=date.today() - timedelta(days=54),
        )
        db.add(wo3)
        db.flush()
        db.add(MaintenanceRecord(work_order_id=wo3.id, event="ASSIGNED", recorded_by=circle_officer.id))
        db.add(MaintenanceRecord(work_order_id=wo3.id, event="COMPLETED", notes="Desilting completed.", recorded_by=maintenance_officer.id))
        db.add(MaintenanceRecord(work_order_id=wo3.id, event="VERIFIED", recorded_by=circle_officer.id))

        # --- Notifications ---
        db.add(Notification(
            recipient_id=circle_officer.id, event=NotificationEvent.APPROVAL_PENDING,
            title="Maintenance request pending approval", body="Emergency repair request for Old Timber Bridge needs your decision.",
            context={"maintenance_request_id": str(req2.id)},
        ))
        db.add(Notification(
            recipient_id=state_admin.id, event=NotificationEvent.CRITICAL_CONDITION,
            title="Critical asset condition", body="Old Timber Bridge assessed as CRITICAL after inspection.",
            context={"asset_id": str(bridge2.id)},
        ))

        db.commit()
        print("Seed data created successfully.")
        print_credentials()
    finally:
        db.close()


def print_credentials():
    print("\nDemo login credentials (password for all): " + DEMO_PASSWORD)
    for email, role in [
        ("state.admin@rnb.gov.in", "State Admin"),
        ("dept.admin@rnb.gov.in", "Department Admin"),
        ("circle.north@rnb.gov.in", "Circle/Division Officer"),
        ("subdivision.n1a@rnb.gov.in", "Sub-Division Officer"),
        ("field.engineer@rnb.gov.in", "Field Engineer / Inspector"),
        ("maintenance.officer@rnb.gov.in", "Maintenance Officer"),
        ("auditor@rnb.gov.in", "Auditor"),
        ("contractor.user@rnb.gov.in", "Contractor"),
    ]:
        print(f"  {email:35s} {role}")


if __name__ == "__main__":
    run()
