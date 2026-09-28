"""End-to-end tests for the citizen grievance and GeM-style tender modules
(see conftest.py — skipped whole-module if no local Postgres is reachable)."""

from app.models.contractor import Contractor


def _make_contractor(db_session, user, name="Test Contractor"):
    contractor = Contractor(name=name, user_id=user.id)
    db_session.add(contractor)
    db_session.flush()
    return contractor


def test_public_can_file_grievance_without_auth(client, reference_data, make_user, auth_headers):
    admin = make_user("grv.admin@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("grv.admin@example.com")

    res = client.post(
        "/api/v1/grievances",
        data={
            "title": "Pothole near tree root",
            "description": "Tree root water seepage is damaging the asphalt near KM 3.",
            "category": "TREE_HAZARD",
            "severity": "MEDIUM",
            "lat": "18.52",
            "lon": "73.85",
            "reporter_name": "A Citizen",
        },
    )
    assert res.status_code == 201, res.text
    grievance = res.json()
    assert grievance["status"] == "OPEN"
    assert grievance["location"]["type"] == "Point"

    # unauthenticated listing is rejected...
    assert client.get("/api/v1/grievances").status_code == 401
    # ...but staff can see it
    listed = client.get("/api/v1/grievances", headers=admin_headers).json()
    assert any(g["id"] == grievance["id"] for g in listed)

    make_user("grv.contractor@example.com", "CONTRACTOR", reference_data["division"])
    contractor_headers = auth_headers("grv.contractor@example.com")
    assert client.get("/api/v1/grievances", headers=contractor_headers).status_code == 403
    invalid_transition = client.patch(
        f"/api/v1/grievances/{grievance['id']}/status",
        json={"status": "RESOLVED", "notes": "Resolved directly."},
        headers=admin_headers,
    )
    assert invalid_transition.status_code == 409

    geo = client.get("/api/v1/grievances/geojson", headers=admin_headers).json()
    assert any(f["properties"]["id"] == grievance["id"] for f in geo["features"])


def test_grievance_resolve_and_convert_to_maintenance(client, reference_data, make_user, auth_headers):
    admin = make_user("grv.admin2@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("grv.admin2@example.com")

    asset = client.post("/api/v1/assets", json={
        "asset_code": "RB-GRV-0001", "name": "Grievance Test Road", "asset_type_code": "ROAD",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
    }, headers=admin_headers).json()

    filed = client.post(
        "/api/v1/grievances",
        data={
            "title": "Deep pothole", "description": "Root damage causing a growing pothole.",
            "category": "POTHOLE", "severity": "HIGH", "lat": "18.5", "lon": "73.8", "asset_id": asset["id"],
        },
    ).json()

    converted = client.post(f"/api/v1/grievances/{filed['id']}/convert-to-maintenance", headers=admin_headers)
    assert converted.status_code == 200, converted.text
    maintenance_request_id = converted.json()["maintenance_request_id"]

    reqs = client.get("/api/v1/maintenance/requests", headers=admin_headers).json()
    assert any(r["id"] == maintenance_request_id for r in reqs)

    resolved = client.patch(
        f"/api/v1/grievances/{filed['id']}/status",
        json={"status": "RESOLVED", "notes": "Pothole patched and tree root trimmed."},
        headers=admin_headers,
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "RESOLVED"
    assert resolved.json()["resolved_by"] is not None


def test_grievance_conversion_requires_linked_asset(client, reference_data, auth_headers, make_user):
    make_user("grv.admin3@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("grv.admin3@example.com")

    filed = client.post(
        "/api/v1/grievances",
        data={"title": "Unlinked issue", "description": "No asset yet.", "category": "OTHER", "severity": "LOW", "lat": "18.5", "lon": "73.8"},
    ).json()

    res = client.post(f"/api/v1/grievances/{filed['id']}/convert-to-maintenance", headers=admin_headers)
    assert res.status_code == 400


def test_tender_full_lifecycle_publish_bid_award(client, db_session, reference_data, make_user, auth_headers):
    admin = make_user("tender.admin@example.com", "STATE_ADMIN", reference_data["state"])
    admin_headers = auth_headers("tender.admin@example.com")

    contractor_user = make_user("tender.contractor@example.com", "CONTRACTOR", reference_data["division"])
    contractor = _make_contractor(db_session, contractor_user)
    contractor_headers = auth_headers("tender.contractor@example.com")

    contractor_publish = client.post("/api/v1/tenders", json={
        "title": "Unauthorized tender", "description": "Contractors cannot publish tenders.",
        "department_id": str(reference_data["department"].id),
        "administrative_unit_id": str(reference_data["division"].id),
    }, headers=contractor_headers)
    assert contractor_publish.status_code == 403

    tender = client.post("/api/v1/tenders", json={
        "title": "Resurface SH-12", "description": "Resurfacing works for SH-12 northern stretch.",
        "department_id": str(reference_data["department"].id), "administrative_unit_id": str(reference_data["division"].id),
        "estimated_value": 5000000,
    }, headers=admin_headers).json()
    assert tender["status"] == "PUBLISHED"
    assert tender["tender_number"].startswith("GEM/")

    # a non-contractor cannot bid
    res = client.post(f"/api/v1/tenders/{tender['id']}/bids", json={"bid_amount": 4800000}, headers=admin_headers)
    assert res.status_code == 403

    bid = client.post(f"/api/v1/tenders/{tender['id']}/bids", json={"bid_amount": 4800000, "remarks": "12 week timeline"}, headers=contractor_headers)
    assert bid.status_code == 201, bid.text
    bid_id = bid.json()["id"]

    contractor_two_user = make_user("tender.contractor2@example.com", "CONTRACTOR", reference_data["division"])
    _make_contractor(db_session, contractor_two_user, "Second Test Contractor")
    contractor_two_headers = auth_headers("tender.contractor2@example.com")
    competing_bid = client.post(f"/api/v1/tenders/{tender['id']}/bids", json={"bid_amount": 4700000}, headers=contractor_two_headers)
    assert competing_bid.status_code == 201

    bidder_view = client.get("/api/v1/tenders", headers=contractor_headers).json()
    visible_tender = next(item for item in bidder_view if item["id"] == tender["id"])
    assert len(visible_tender["bids"]) == 1
    assert visible_tender["bids"][0]["id"] == bid_id
    assert visible_tender["bid_count"] == 0
    my_bids = client.get("/api/v1/tenders/my-bids", headers=contractor_headers).json()
    assert len(my_bids) == 1 and my_bids[0]["bids"][0]["id"] == bid_id

    # duplicate bid from the same contractor is rejected
    dup = client.post(f"/api/v1/tenders/{tender['id']}/bids", json={"bid_amount": 4700000}, headers=contractor_headers)
    assert dup.status_code == 409

    detail = client.get(f"/api/v1/tenders/{tender['id']}", headers=admin_headers).json()
    assert detail["bid_count"] == 2

    premature_award = client.post(f"/api/v1/tenders/{tender['id']}/award", json={"bid_id": bid_id}, headers=admin_headers)
    assert premature_award.status_code == 400
    client.post(f"/api/v1/tenders/{tender['id']}/close", headers=admin_headers)

    awarded = client.post(f"/api/v1/tenders/{tender['id']}/award", json={"bid_id": bid_id}, headers=admin_headers)
    assert awarded.status_code == 200, awarded.text
    assert awarded.json()["status"] == "AWARDED"
    assert awarded.json()["awarded_bid_id"] == bid_id

    bidder_result = client.get(f"/api/v1/tenders/{tender['id']}", headers=contractor_two_headers).json()
    assert {item["id"] for item in bidder_result["bids"]} == {bid_id, competing_bid.json()["id"]}

    # bidding is closed once awarded
    late_bid = client.post(f"/api/v1/tenders/{tender['id']}/bids", json={"bid_amount": 4000000}, headers=contractor_headers)
    assert late_bid.status_code == 400
