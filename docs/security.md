# Security

## Authentication

JWT access + refresh tokens (`app/auth/security.py`). Access tokens are short-lived
(`ACCESS_TOKEN_EXPIRE_MINUTES`, default 30 min); refresh tokens are longer-lived (default 7 days).
Passwords are hashed with bcrypt (`passlib`). No plaintext password ever leaves `app/auth/security.py`.

Government SSO / OIDC is **not implemented** in the MVP — `app/auth/` is the single integration
point where an OIDC flow would replace the password grant later without touching authorization logic.

## Authorization

- **RBAC**: every write endpoint (and most reads) is gated by `Depends(require_roles(...))`
  (`app/auth/deps.py`), checked against the caller's actual role grants in the database — never
  trusting a client-supplied role claim beyond what's embedded in a token the server itself issued.
- **Jurisdiction scoping**: `app/permissions/jurisdiction.py` restricts list queries to a user's
  administrative-unit subtree via a materialized-path prefix filter, applied server-side
  (`apply_jurisdiction_filter`) — the frontend hiding a menu item is a UX nicety, not the security
  boundary.
- The frontend (`hooks/useAuth.tsx`) hides unauthorized actions for UX, but every one of those
  actions is independently re-checked by the backend.

## Input validation

- Request bodies are validated by Pydantic schemas (`app/schemas/`) before touching the database.
- All database access goes through SQLAlchemy's ORM/Core query builder — no raw string-interpolated
  SQL, so standard SQL injection vectors don't apply.
- File uploads (`app/utils/storage.py`) are validated by extension and size
  (`ALLOWED_UPLOAD_EXTENSIONS`, `MAX_UPLOAD_SIZE_MB`) before being written to disk; the storage key
  is server-generated (UUID-based), never taken from user input, so there's no path-traversal
  surface from the filename.

## CORS

`BACKEND_CORS_ORIGINS` in `.env` is an explicit allow-list (defaults to the local dev frontend
origin only). Tighten this to the deployed frontend origin(s) before any non-local deployment.

## Secrets

All configuration (`SECRET_KEY`, database URL, CORS origins) is environment-driven
(`app/config.py`, `.env` / `.env.example`) — nothing is hardcoded, and `.env` is gitignored.
**Rotate `SECRET_KEY` before any real deployment** — the checked-in `.env.example` value is a
placeholder, not a secret.

## Audit trail

Every material state change (asset create/update, lifecycle transitions, inspection submit/review,
maintenance decisions, work order status changes, document upload/versioning, user/role changes,
grievance and tender actions) write immutable rows to `audit_logs` (`app/utils/audit.py`) in the same
database transaction as the change itself — so an audit entry can never be missing because a background
job failed to run.

## Rate limiting

Not implemented in the MVP (no reverse proxy in front of the app to enforce it at). For a real
deployment, add rate limiting at whichever edge sits in front of FastAPI (a reverse proxy, API
gateway, or `slowapi`/`starlette` middleware).

## Deliberately out of scope for the MVP (future work)

- Government SSO/OIDC, MFA
- Centralized secrets management (currently plain `.env`)
- Per-document `access_roles` enforcement (the column exists on `documents` but isn't yet checked
  on download — every authenticated user can currently download any document)
- Network segmentation / production hardening — this is a hackathon demo, not a hardened deployment
