-- Initialize staging database
-- This script runs when the PostgreSQL container starts for the first time

-- Ensure the database exists (already created by POSTGRES_DB env var)
-- Create any additional extensions if needed

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create read-only user for monitoring (optional)
-- CREATE USER beryl3_readonly WITH PASSWORD 'readonly_password_change_this';
-- GRANT CONNECT ON DATABASE beryl3_staging TO beryl3_readonly;
-- GRANT USAGE ON SCHEMA public TO beryl3_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO beryl3_readonly;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO beryl3_readonly;