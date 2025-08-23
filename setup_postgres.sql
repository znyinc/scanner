-- PostgreSQL setup script for Stock Scanner
-- Run this script as the postgres superuser

-- Create the database
CREATE DATABASE stock_scanner;

-- Create the user with password
CREATE USER stock_scanner WITH PASSWORD 'password123';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE stock_scanner TO stock_scanner;

-- Connect to the stock_scanner database
\c stock_scanner;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO stock_scanner;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO stock_scanner;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO stock_scanner;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Display confirmation
SELECT 'PostgreSQL setup completed successfully!' as status;