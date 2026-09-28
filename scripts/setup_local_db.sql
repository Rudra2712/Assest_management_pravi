-- Run once, as the postgres superuser, to create the app's database role and
-- database for local development. Safe to re-run (guards with IF NOT EXISTS
-- where Postgres allows it).
--
-- Usage (PowerShell), from the PostgreSQL bin directory or with it on PATH:
--   psql -U postgres -f scripts\setup_local_db.sql

\set ON_ERROR_STOP on

DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'rb_admin') THEN
      CREATE ROLE rb_admin LOGIN PASSWORD 'rb_dev_password';
   END IF;
END
$$;

ALTER ROLE rb_admin WITH LOGIN PASSWORD 'rb_dev_password';

SELECT 'CREATE DATABASE rb_assets OWNER rb_admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'rb_assets')\gexec

\c rb_assets
GRANT ALL PRIVILEGES ON DATABASE rb_assets TO rb_admin;
GRANT ALL ON SCHEMA public TO rb_admin;

-- Separate database for the automated test suite (backend/tests/), so a test
-- run can never touch real dev/demo data in rb_assets.
SELECT 'CREATE DATABASE rb_assets_test OWNER rb_admin'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'rb_assets_test')\gexec

\c rb_assets_test
GRANT ALL PRIVILEGES ON DATABASE rb_assets_test TO rb_admin;
GRANT ALL ON SCHEMA public TO rb_admin;
