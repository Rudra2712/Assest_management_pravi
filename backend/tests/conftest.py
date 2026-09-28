"""Integration test fixtures. These need a real local PostgreSQL + PostGIS
database (DATABASE_URL from .env / environment) — there is no SQLite fallback
since the schema uses PostGIS geometry and JSONB columns. If the database
isn't reachable or PostGIS isn't installed, the whole integration suite is
skipped rather than failing noisily; app/services/test_*.py (pure unit tests)
always run regardless."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app import models  # noqa: F401  -- registers all tables on Base.metadata
from app.main import app


def _database_available() -> bool:
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        engine.dispose()
        return True
    except Exception:
        return False


DB_AVAILABLE = _database_available()


@pytest.fixture(scope="session")
def engine():
    if not DB_AVAILABLE:
        pytest.skip("Local PostgreSQL + PostGIS not available (see docs/setup.md)")
    eng = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
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

    dept = Department(code="RNB", name="Roads & Buildings")
    db_session.add(dept)
    db_session.flush()

    state = AdministrativeUnit(code="ST", name="State", level=AdminUnitLevel.STATE, path="")
    db_session.add(state)
    db_session.flush()
    state.path = str(state.id)

    division = AdministrativeUnit(code="DIV1", name="Division 1", level=AdminUnitLevel.DIVISION, parent_id=state.id, path="")
    db_session.add(division)
    db_session.flush()
    division.path = f"{state.path}.{division.id}"

    other_division = AdministrativeUnit(code="DIV2", name="Division 2", level=AdminUnitLevel.DIVISION, parent_id=state.id, path="")
    db_session.add(other_division)
    db_session.flush()
    other_division.path = f"{state.path}.{other_division.id}"

    road_type = AssetType(code=AssetTypeCode.ROAD, name="Road", default_geometry_kind=GeometryKind.LINESTRING)
    bridge_type = AssetType(code=AssetTypeCode.BRIDGE, name="Bridge", default_geometry_kind=GeometryKind.POINT)
    db_session.add_all([road_type, bridge_type])

    roles = {}
    for role in SystemRole:
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
