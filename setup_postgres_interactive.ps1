# Interactive PostgreSQL Setup for Stock Scanner
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stock Scanner PostgreSQL Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will help you set up PostgreSQL for the Stock Scanner." -ForegroundColor Yellow
Write-Host "You'll need to know the PostgreSQL 'postgres' user password." -ForegroundColor Yellow
Write-Host ""

Write-Host "If you don't know the postgres password, you can:" -ForegroundColor White
Write-Host "1. Check your PostgreSQL installation notes" -ForegroundColor White
Write-Host "2. Try common passwords like: postgres, admin, password" -ForegroundColor White
Write-Host "3. Reset the password (see POSTGRES_SETUP_GUIDE.md)" -ForegroundColor White
Write-Host ""

# Get postgres password from user
$postgresPassword = Read-Host "Enter the postgres user password" -AsSecureString
$postgresPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($postgresPassword))

Write-Host ""
Write-Host "Step 1: Testing PostgreSQL connection..." -ForegroundColor Green

# Test connection
$env:PGPASSWORD = $postgresPasswordPlain
$testResult = psql -U postgres -d postgres -c "SELECT 'PostgreSQL is working!' as status;" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Could not connect to PostgreSQL." -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "- PostgreSQL service is running" -ForegroundColor Yellow
    Write-Host "- You have the correct postgres password" -ForegroundColor Yellow
    Write-Host "- PostgreSQL is listening on port 5432" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host ""
Write-Host "SUCCESS: Connected to PostgreSQL!" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Creating database and user..." -ForegroundColor Green
Write-Host ""

# Create database and user
$commands = @(
    "CREATE DATABASE stock_scanner;",
    "CREATE USER stock_scanner WITH PASSWORD 'password123';",
    "GRANT ALL PRIVILEGES ON DATABASE stock_scanner TO stock_scanner;",
    "\c stock_scanner",
    "GRANT ALL ON SCHEMA public TO stock_scanner;",
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO stock_scanner;",
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO stock_scanner;",
    "CREATE EXTENSION IF NOT EXISTS ""uuid-ossp"";"
)

foreach ($cmd in $commands) {
    Write-Host "Executing: $cmd" -ForegroundColor Gray
    if ($cmd -eq "\c stock_scanner") {
        # Connect to the new database
        continue
    }
    
    if ($cmd.Contains("stock_scanner")) {
        $result = psql -U postgres -d stock_scanner -c $cmd 2>&1
    } else {
        $result = psql -U postgres -d postgres -c $cmd 2>&1
    }
    
    if ($LASTEXITCODE -ne 0 -and $result -notlike "*already exists*") {
        Write-Host "Warning: Command failed - $result" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Step 3: Testing new user connection..." -ForegroundColor Green
Write-Host ""

# Test new user connection
$env:PGPASSWORD = "password123"
$testUserResult = psql -U stock_scanner -d stock_scanner -c "SELECT 'Connection successful!' as status;" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS! PostgreSQL setup complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Database: stock_scanner" -ForegroundColor Cyan
    Write-Host "User: stock_scanner" -ForegroundColor Cyan
    Write-Host "Password: password123" -ForegroundColor Cyan
    Write-Host "Host: localhost" -ForegroundColor Cyan
    Write-Host "Port: 5432" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now run the Stock Scanner application!" -ForegroundColor Green
    Write-Host ""
    
    # Test the Python connection
    Write-Host "Step 4: Testing Python database connection..." -ForegroundColor Green
    Set-Location backend
    python test_connection.py
    Set-Location ..
    
} else {
    Write-Host ""
    Write-Host "ERROR: Could not connect with new user." -ForegroundColor Red
    Write-Host "Please check the setup manually." -ForegroundColor Yellow
    Write-Host ""
}

# Clear password from environment
$env:PGPASSWORD = ""

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")