@echo off
echo Setting up PostgreSQL for Stock Scanner...
echo.

echo Step 1: Setting PostgreSQL password for postgres user
echo Please run this command and set a password for the postgres user:
echo.
echo psql -U postgres -c "ALTER USER postgres PASSWORD 'admin123';"
echo.
pause

echo Step 2: Creating database and user
echo Running setup script...
psql -U postgres -f setup_postgres.sql

echo.
echo Step 3: Testing connection
echo Testing connection to the new database...
psql -U stock_scanner -d stock_scanner -c "SELECT 'Connection successful!' as status;"

echo.
echo Setup complete! Your PostgreSQL configuration:
echo - Database: stock_scanner
echo - User: stock_scanner  
echo - Password: password123
echo - Host: localhost
echo - Port: 5432
echo.
pause