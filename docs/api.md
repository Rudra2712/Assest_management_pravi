# API

Base path: `/api/v1`. Interactive OpenAPI docs at `http://localhost:8000/docs` once the backend is
running. Auth: `Authorization: Bearer <access_token>` (JWT, short-lived; refresh via `/auth/refresh`).

## Endpoint groups

| Prefix | Covers |
|---|---|
| `/auth` | `POST /login`, `POST /refresh`, `GET /me` |
| `/users` | List/create users, grant roles |
| `/departments`, `/admin-units` | Reference data for org structure |
| `/asset-types`, `/asset-types/categories` | Asset type/category reference data |
| `/assets` | List (paginated, filterable, jurisdiction-scoped), create, get, update, lifecycle transitions + history |
| `/gis` | `GET /assets.geojson`, `GET /nearby.geojson` — GeoJSON FeatureCollections for the map |
| `/inspections` | Assign, list, get, submit (checklist/findings/GPS/photos), review (approve/return) |
| `/condition` | Condition history per asset, manual recompute |
| `/maintenance` | Maintenance requests: create, list, approve/reject, convert to work order |
| `/work-orders` | Assign, start, complete, verify, history |
| `/projects` | CRUD + linking assets to a project |
| `/contractors` | List/create |
| `/documents` | Upload (multipart), list by linked entity, download, new version, delete |
| `/approvals` | List approval records (inspection/maintenance/lifecycle/project) |
| `/notifications` | List mine, mark read |
| `/reports` | `/dashboard` (state/GIS-level aggregates), `/field-dashboard` (per-inspector) |
| `/audit-logs` | Filterable audit trail (state/department admin only) |

## Conventions

- **Pagination**: list endpoints that can grow large (`/assets`) return `{items, total, page,
  page_size, pages}`; smaller reference-style lists return a plain array.
- **Filtering**: query parameters on list endpoints (`asset_type_code`, `lifecycle_status`,
  `current_condition`, `administrative_unit_id`, `q`, …).
- **Errors**: standard FastAPI `{"detail": "..."}` with the appropriate HTTP status
  (400 validation, 401 unauthenticated, 403 unauthorized, 404 not found, 409 conflict).
- **Authorization**: every write endpoint declares the roles allowed to call it via
  `Depends(require_roles(...))`; list endpoints apply jurisdiction scoping via
  `apply_jurisdiction_filter(...)`. This is enforced server-side regardless of what the frontend hides.
