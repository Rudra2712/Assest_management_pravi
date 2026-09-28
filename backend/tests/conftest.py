"""Integration test fixtures.

These run against a SEPARATE database (DATABASE_URL's name + "_test") —
never the real dev database — so a broken test run can't truncate or corrupt
real seeded/demo data. scripts/setup_local_db.sql creates both databases.
Override with TEST_DATABASE_URL if you want to point elsewhere.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app import models  # noqa: F401  -- registers all tables on Base.metadata
from app.main import app


def _test_database_url() -> str:
    override = os.environ.get("TEST_DATABASE_URL")
    if override:
        return override
    url = make_url(settings.DATABASE_URL)
    return str(url.set(database=f"{url.database}_test"))


TEST_DATABASE_URL = _test_database_url()


def _database_available() -> bool:
    try:
        engine = create_engine(TEST_DATABASE_URL)
        with engine.connect():
            pass
        engine.dispose()
        return True
    except Exception:
        return False


DB_AVAILABLE = _database_available()


@pytest.fixture(scope="session")
def engine():
    if not DB_AVAILABLE:
        pytest.skip(f"Test database not available at {TEST_DATABASE_URL} (see docs/setup.md)")
    eng = create_engine(TEST_DATABASE_URL)
    # checkfirst=True (the default) — never drops anything. This is an
    # isolated, disposable schema; each test's data is rolled back via the
    # SAVEPOINT in db_session below, so there's nothing to clean up here.
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine):
    """Each test runs inside an outer transaction + a SAVEPOINT. Application
    code (routers) calling session.commit() only releases the SAVEPOINT — a
    new one is opened immediately — so the outer transaction (and therefore
    the whole test's writes) is always rolled back at teardown."""

    connection = engine.connect()
    outer_transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = SessionLocal()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def reference_data(db_session):
    from app.models.enums import AdminUnitLevel, AssetTypeCode, GeometryKind, SystemRole
    from app.models.geo import AdministrativeUnit, Department
    from app.models.asset import AssetType
    from app.models.user import Role

    # Idempotent (query-or-create): the local dev database this test suite runs
    # against may already have real seed data (python -m seed.seed_data) with
    # overlapping reference codes — reuse it rather than colliding with it.
    def get_or_create(model, code, **kwargs):
        existing = db_session.query(model).filter(model.code == code).first()
        if existing:
            return existing
        obj = model(code=code, **kwargs)
        db_session.add(obj)
        db_session.flush()
        return obj

    dept = get_or_create(Department, "TEST-RNB", name="Roads & Buildings (test)")

    state = get_or_create(AdministrativeUnit, "TEST-ST", name="State (test)", level=AdminUnitLevel.STATE, path="")
    if not state.path:
        state.path = str(state.id)
        db_session.flush()

    division = get_or_create(AdministrativeUnit, "TEST-DIV1", name="Division 1 (test)", level=AdminUnitLevel.DIVISION, parent_id=state.id, path="")
    if not division.path:
        division.path = f"{state.path}.{division.id}"
        db_session.flush()

    other_division = get_or_create(AdministrativeUnit, "TEST-DIV2", name="Division 2 (test)", level=AdminUnitLevel.DIVISION, parent_id=state.id, path="")
    if not other_division.path:
        other_division.path = f"{state.path}.{other_division.id}"
        db_session.flush()

    asset_type_defs = [
        (AssetTypeCode.ROAD, "Road", GeometryKind.LINESTRING),
        (AssetTypeCode.BRIDGE, "Bridge", GeometryKind.POINT),
        (AssetTypeCode.CULVERT, "Culvert", GeometryKind.POINT),
        (AssetTypeCode.BUILDING, "Building", GeometryKind.POLYGON),
        (AssetTypeCode.PUBLIC_STRUCTURE, "Public Structure", GeometryKind.POINT),
        (AssetTypeCode.OTHER_FIXED_ASSET, "Other Fixed Asset", GeometryKind.POINT),
    ]
    asset_types = {}
    for code, name, geom_kind in asset_type_defs:
        t = db_session.query(AssetType).filter(AssetType.code == code).first()
        if not t:
            t = AssetType(code=code, name=name, default_geometry_kind=geom_kind)
            db_session.add(t)
        asset_types[code.value] = t
    road_type = asset_types[AssetTypeCode.ROAD.value]
    bridge_type = asset_types[AssetTypeCode.BRIDGE.value]

    roles = {}
    for role in SystemRole:
        r = db_session.query(Role).filter(Role.code == role.value).first()
        if not r:
            r = Role(code=role.value, name=role.value)
            db_session.add(r)
        roles[role.value] = r

    db_session.flush()

    return {
        "department": dept,
        "state": state,
        "division": division,
        "other_division": other_division,
        "road_type": road_type,
        "bridge_type": bridge_type,
        "asset_types": asset_types,
        "roles": roles,
    }


@pytest.fixture()
def make_user(db_session, reference_data):
    from app.auth.security import hash_password
    from app.models.user import User, UserRole

    def _make(email, role_code, admin_unit):
        user = User(
            email=email, full_name=email, hashed_password=hash_password("Password123!"),
            department_id=reference_data["department"].id, administrative_unit_id=admin_unit.id,
        )
        db_session.add(user)
        db_session.flush()
        db_session.add(UserRole(user_id=user.id, role_id=reference_data["roles"][role_code].id, jurisdiction_unit_id=admin_unit.id))
        db_session.flush()
        return user

    return _make


@pytest.fixture()
def auth_headers(client):
    def _headers(email, password="Password123!"):
        res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert res.status_code == 200, res.text
        token = res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _headers
