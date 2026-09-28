"""End-to-end API tests against a real local PostgreSQL + PostGIS database
(see conftest.py — the whole module is skipped if one isn't reachable)."""


def test_login_and_me(client, reference_data, make_user):
    make_user("admin@example.com", "STATE_ADMIN", reference_data["state"])
    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Password123!"})
    assert res.status_code == 200
    assert "access_token" in res.json()

    res = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert res.status_code == 401

    headers = {"Authorization": f"Bearer {client.post('/api/v1/auth/login', json={'email': 'admin@example.com', 'password': 'Password123!'}).json()['access_token']}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "admin@example.com"
    assert "STATE_ADMIN" in res.json()["roles"]


def test_asset_create_and_lifecycle_transition(client, reference_data, make_user, auth_headers):
    make_user("admin2@example.com", "STATE_ADMIN", reference_data["state"])
    headers = auth_headers("admin2@example.com")

    payload = {
        "asset_code": "RB-TEST-0001",
        "name": "Test Road",
        "asset_type_code": "ROAD",
        "department_id": str(reference_data["department"].id),
        "administrative_unit_id": str(reference_data["division"].id),
        "geometry": {"type": "LineString", "coordinates": [[73.8, 18.5], [73.9, 18.6]]},
        "road": {"length_km": 5.2, "number_of_lanes": 2},
    }
    res = client.post("/api/v1/assets", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    asset = res.json()
    assert asset["lifecycle_status"] == "PLANNED"
    assert asset["road"]["length_km"] == 5.2
    assert asset["geometry"]["type"] == "LineString"

    # invalid transition rejected
    res = client.post(f"/api/v1/assets/{asset['id']}/lifecycle-transitions", json={"new_status": "OPERATIONAL"}, headers=headers)
    assert res.status_code == 400

    # valid transition chain
    for status in ["SANCTIONED", "UNDER_CONSTRUCTION", "COMMISSIONED", "OPERATIONAL"]:
        res = client.post(f"/api/v1/assets/{asset['id']}/lifecycle-transitions", json={"new_status": status}, headers=headers)
        assert res.status_code == 200, res.text
        assert res.json()["lifecycle_status"] == status

    history = client.get(f"/api/v1/assets/{asset['id']}/lifecycle-history", headers=headers).json()
    assert len(history) == 4


def test_duplicate_asset_code_rejected(client, reference_data, make_user, auth_headers):
    make_user("admin3@example.com", "STATE_ADMIN", reference_data["state"])
    headers = auth_headers("admin3@example.com")
    payload = {
        "asset_code": "RB-TEST-DUP",
        "name": "Dup Asset",
        "asset_type_code": "BRIDGE",
        "department_id": str(reference_data["department"].id),
        "administrative_unit_id": str(reference_data["division"].id),
    }
    assert client.post("/api/v1/assets", json=payload, headers=headers).status_code == 201
    res = client.post("/api/v1/assets", json=payload, headers=headers)
    assert res.status_code == 409


def test_jurisdiction_scoping_hides_assets_outside_subtree(client, reference_data, make_user, auth_headers):
    admin = make_user("admin4@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("admin4@example.com")

    client.post("/api/v1/assets", json={
        "asset_code": "RB-DIV1-0001", "name": "Division 1 Bridge", "asset_type_code": "BRIDGE",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
    }, headers=admin_headers)
    client.post("/api/v1/assets", json={
        "asset_code": "RB-DIV2-0001", "name": "Division 2 Bridge", "asset_type_code": "BRIDGE",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["other_division"].id),
    }, headers=admin_headers)

    make_user("officer.div1@example.com", "SUB_DIVISION_OFFICER", reference_data["division"])
    officer_headers = auth_headers("officer.div1@example.com")

    res = client.get("/api/v1/assets", headers=officer_headers)
    names = {item["name"] for item in res.json()["items"]}
    assert "Division 1 Bridge" in names
    assert "Division 2 Bridge" not in names

    # the state admin (jurisdiction-wide role) sees both
    res = client.get("/api/v1/assets", headers=admin_headers)
    names = {item["name"] for item in res.json()["items"]}
    assert {"Division 1 Bridge", "Division 2 Bridge"} <= names


def test_gis_geojson_returns_feature_for_created_asset(client, reference_data, make_user, auth_headers):
    make_user("admin5@example.com", "STATE_ADMIN", reference_data["state"])
    headers = auth_headers("admin5@example.com")
    client.post("/api/v1/assets", json={
        "asset_code": "RB-GIS-0001", "name": "GIS Test Bridge", "asset_type_code": "BRIDGE",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
        "geometry": {"type": "Point", "coordinates": [73.85, 18.52]},
    }, headers=headers)

    res = client.get("/api/v1/gis/assets.geojson", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["type"] == "FeatureCollection"
    names = {f["properties"]["name"] for f in body["features"]}
    assert "GIS Test Bridge" in names


def test_inspection_submit_creates_condition_assessment(client, reference_data, make_user, auth_headers):
    make_user("admin6@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("admin6@example.com")
    inspector = make_user("inspector1@example.com", "FIELD_ENGINEER", reference_data["division"])
    inspector_headers = auth_headers("inspector1@example.com")

    asset = client.post("/api/v1/assets", json={
        "asset_code": "RB-INSP-0001", "name": "Inspection Test Bridge", "asset_type_code": "BRIDGE",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
    }, headers=admin_headers).json()

    inspection = client.post("/api/v1/inspections", json={
        "asset_id": asset["id"], "inspector_id": str(inspector.id),
    }, headers=admin_headers).json()

    res = client.post(f"/api/v1/inspections/{inspection['id']}/submit", json={
        "inspection_date": "2026-01-01", "overall_condition": "POOR",
        "findings": [{"description": "Crack in deck", "severity": "HIGH", "recommends_maintenance": True}],
    }, headers=inspector_headers)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "SUBMITTED"

    asset_after = client.get(f"/api/v1/assets/{asset['id']}", headers=admin_headers).json()
    assert asset_after["current_condition"] == "POOR"

    history = client.get(f"/api/v1/condition/assets/{asset['id']}/history", headers=admin_headers).json()
    assert len(history) == 1
    assert history[0]["condition_rating"] == "POOR"
    assert "age" in history[0]["factor_inputs"]


def test_maintenance_workflow_request_to_work_order(client, reference_data, make_user, auth_headers):
    admin = make_user("admin7@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("admin7@example.com")

    asset = client.post("/api/v1/assets", json={
        "asset_code": "RB-MAINT-0001", "name": "Maintenance Test Culvert", "asset_type_code": "CULVERT",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
    }, headers=admin_headers).json()

    req = client.post("/api/v1/maintenance/requests", json={
        "asset_id": asset["id"], "maintenance_type": "CORRECTIVE", "priority": "HIGH", "description": "Repair inlet",
    }, headers=admin_headers).json()
    assert req["status"] == "OPEN"

    decided = client.post(f"/api/v1/maintenance/requests/{req['id']}/decision", json={"approve": True}, headers=admin_headers).json()
    assert decided["status"] == "APPROVED"

    wo = client.post(f"/api/v1/maintenance/requests/{req['id']}/work-order", json={}, headers=admin_headers).json()
    assert wo["status"] == "CREATED"

    # cannot create a second work order for the same request
    res = client.post(f"/api/v1/maintenance/requests/{req['id']}/work-order", json={}, headers=admin_headers)
    assert res.status_code in (400, 409)

    res = client.post(f"/api/v1/work-orders/{wo['id']}/assign", json={"assigned_officer_id": str(admin.id)}, headers=admin_headers)
    assert res.json()["status"] == "ASSIGNED"
    res = client.post(f"/api/v1/work-orders/{wo['id']}/start", headers=admin_headers)
    assert res.json()["status"] == "IN_PROGRESS"
    res = client.post(f"/api/v1/work-orders/{wo['id']}/complete", json={"actual_cost": 1000, "completion_remarks": "done"}, headers=admin_headers)
    assert res.json()["status"] == "COMPLETED"
    res = client.post(f"/api/v1/work-orders/{wo['id']}/verify", json={"verified": True}, headers=admin_headers)
    assert res.json()["status"] == "CLOSED"


def test_document_upload_and_metadata(client, reference_data, make_user, auth_headers):
    make_user("admin8@example.com", "STATE_ADMIN", reference_data["state"])
    headers = auth_headers("admin8@example.com")
    asset = client.post("/api/v1/assets", json={
        "asset_code": "RB-DOC-0001", "name": "Document Test Asset", "asset_type_code": "BRIDGE",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
    }, headers=headers).json()

    res = client.post(
        "/api/v1/documents",
        data={"document_type": "PHOTOGRAPH", "linked_entity_type": "asset", "linked_entity_id": asset["id"]},
        files={"file": ("test.txt", b"hello world", "text/plain")},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    doc = res.json()
    assert doc["filename"] == "test.txt"
    assert doc["current_version"] == 1

    listed = client.get("/api/v1/documents", params={"linked_entity_type": "asset", "linked_entity_id": asset["id"]}, headers=headers).json()
    assert len(listed) == 1

    downloaded = client.get(f"/api/v1/documents/{doc['id']}/download", headers=headers)
    assert downloaded.status_code == 200
    assert downloaded.content == b"hello world"


def test_audit_log_created_on_asset_create(client, reference_data, make_user, auth_headers):
    make_user("auditor1@example.com", "AUDITOR", reference_data["state"])
    make_user("admin9@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("admin9@example.com")
    auditor_headers = auth_headers("auditor1@example.com")

    asset = client.post("/api/v1/assets", json={
        "asset_code": "RB-AUDIT-0001", "name": "Audit Test Asset", "asset_type_code": "BRIDGE",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
    }, headers=admin_headers).json()

    res = client.get("/api/v1/audit-logs", params={"entity_type": "asset", "entity_id": asset["id"]}, headers=auditor_headers)
    assert res.status_code == 200
    logs = res.json()
    assert any(log["action"] == "ASSET_CREATE" for log in logs)


def test_csv_import_preview_flags_missing_columns(client, reference_data, make_user, auth_headers):
    make_user("importer1@example.com", "STATE_ADMIN", reference_data["state"])
    headers = auth_headers("importer1@example.com")
    bad_csv = b"name,asset_type_code\nSome Road,ROAD\n"
    res = client.post("/api/v1/imports/assets/preview", files={"file": ("bad.csv", bad_csv, "text/csv")}, headers=headers)
    assert res.status_code == 400
    assert "asset_code" in res.json()["detail"]


def test_csv_import_commit_skips_duplicates(client, reference_data, make_user, auth_headers):
    make_user("importer2@example.com", "STATE_ADMIN", reference_data["state"])
    headers = auth_headers("importer2@example.com")

    client.post("/api/v1/assets", json={
        "asset_code": "RB-CSV-0001", "name": "Existing Asset", "asset_type_code": "ROAD",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
    }, headers=headers)

    csv_content = (
        "asset_code,name,asset_type_code,department_code,administrative_unit_code\n"
        f"RB-CSV-0001,Existing Asset,ROAD,{reference_data['department'].code},{reference_data['division'].code}\n"
        f"RB-CSV-0002,New Asset,ROAD,{reference_data['department'].code},{reference_data['division'].code}\n"
    ).encode()

    preview = client.post("/api/v1/imports/assets/preview", files={"file": ("assets.csv", csv_content, "text/csv")}, headers=headers).json()
    assert preview["duplicate_count"] == 1
    assert preview["importable_count"] == 1

    result = client.post("/api/v1/imports/assets/commit", files={"file": ("assets.csv", csv_content, "text/csv")}, headers=headers).json()
    assert result["imported"] == 1
    assert result["skipped_duplicates"] == 1

    listed = client.get("/api/v1/assets", params={"q": "New Asset"}, headers=headers).json()
    assert listed["total"] == 1
