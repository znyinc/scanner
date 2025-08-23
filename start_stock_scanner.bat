@echo off
echo ========================================
echo Starting Stock Scanner Application
echo ========================================
echo.

echo Step 1: Starting PostgreSQL Docker container...
docker start stock-scanner-db
if %ERRORLEVEL% NEQ 0 (
    echo Creating new PostgreSQL container...
    docker run --name stock-scanner-db -e POSTGRES_PASSWORD=password123 -e POSTGRES_DB=stock_scanner -p 5433:5432 -d postgres:13
)

echo Waiting for database to be ready...
timeout /t 5

echo Step 2: Starting backend server...
cd backend
start "Backend Server" cmd /k "python run_server.py"

echo Step 3: Starting frontend...
cd ../frontend
start "Frontend Server" cmd /k "npm start"

echo.
echo ========================================
echo Stock Scanner is starting!
echo ========================================
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause > nul