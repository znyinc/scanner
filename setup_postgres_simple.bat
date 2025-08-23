@echo off
echo ========================================
echo Stock Scanner PostgreSQL Setup
echo ========================================
echo.

echo This script will help you set up PostgreSQL for the Stock Scanner.
echo You'll need to know the PostgreSQL 'postgres' user password.
echo.

echo If you don't know the postgres password, you can:
echo 1. Check your PostgreSQL installation notes
echo 2. Try common passwords like: postgres, admin, password
echo 3. Reset the password (see POSTGRES_SETUP_GUIDE.md)
echo.

pause

echo.
echo Step 1: Testing PostgreSQL connection...
echo Enter the postgres user password when prompted:
echo.

psql -U postgres -d postgres -c "SELECT 'PostgreSQL is working!' as status;"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Could not connect to PostgreSQL.
    echo Please check:
    echo - PostgreSQL service is running
    echo - You have the correct postgres password
    echo - PostgreSQL is listening on port 5432
    echo.
    pause
    exit /b 1
)

echo.
echo SUCCESS: Connected to PostgreSQL!
echo.

echo Step 2: Creating database and user...
echo.

psql -U postgres -d postgres -c "CREATE DATABASE stock_scanner;"
psql -U postgres -d postgres -c "CREATE USER stock_scanner WITH PASSWORD 'password123';"
psql -U postgres -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE stock_scanner TO stock_scanner;"
psql -U postgres -d stock_scanner -c "GRANT ALL ON SCHEMA public TO stock_scanner;"
psql -U postgres -d stock_scanner -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO stock_scanner;"
psql -U postgres -d stock_scanner -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO stock_scanner;"
psql -U postgres -d stock_scanner -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to create database or user.
    echo The database or user might already exist.
    echo.
)

echo.
echo Step 3: Testing new user connection...
echo.

set PGPASSWORD=password123
psql -U stock_scanner -d stock_scanner -c "SELECT 'Connection successful!' as status;"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! PostgreSQL setup complete!
    echo ========================================
    echo.
    echo Database: stock_scanner
    echo User: stock_scanner
    echo Password: password123
    echo Host: localhost
    echo Port: 5432
    echo.
    echo You can now run the Stock Scanner application!
    echo.
) else (
    echo.
    echo ERROR: Could not connect with new user.
    echo Please check the setup manually.
    echo.
)

set PGPASSWORD=
pause