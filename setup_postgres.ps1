# PostgreSQL Setup Script for Stock Scanner
Write-Host "Setting up PostgreSQL for Stock Scanner..." -ForegroundColor Green
Write-Host ""

# Check if PostgreSQL is running
$pgService = Get-Service -Name "postgresql-x64-17" -ErrorAction SilentlyContinue
if ($pgService.Status -ne "Running") {
    Write-Host "PostgreSQL service is not running. Please start it first." -ForegroundColor Red
    exit 1
}

Write-Host "PostgreSQL service is running." -ForegroundColor Green
Write-Host ""

# Try to connect and set up the database
Write-Host "Setting up database and user..." -ForegroundColor Yellow

try {
    # First, try to connect as the current Windows user
    Write-Host "Attempting to connect to PostgreSQL..." -ForegroundColor Yellow
    
    # Run the setup SQL script
    $env:PGPASSWORD = ""  # Clear any existing password
    psql -U $env:USERNAME -d postgres -f setup_postgres.sql
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Database setup completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Setup failed. Trying alternative method..." -ForegroundColor Yellow
        
        # Try with postgres user
        Write-Host "Please enter the postgres user password when prompted:" -ForegroundColor Yellow
        psql -U postgres -f setup_postgres.sql
    }
}
catch {
    Write-Host "Error during setup: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing connection to new database..." -ForegroundColor Yellow

# Test the connection
$env:PGPASSWORD = "password123"
psql -U stock_scanner -d stock_scanner -c "SELECT 'Connection successful!' as status;"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Setup complete! Your PostgreSQL configuration:" -ForegroundColor Green
    Write-Host "   Database: stock_scanner" -ForegroundColor Cyan
    Write-Host "   User: stock_scanner" -ForegroundColor Cyan
    Write-Host "   Password: password123" -ForegroundColor Cyan
    Write-Host "   Host: localhost" -ForegroundColor Cyan
    Write-Host "   Port: 5432" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now run the Stock Scanner application!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Connection test failed. Please check the setup." -ForegroundColor Red
    Write-Host "You may need to manually create the user and database." -ForegroundColor Yellow
}

# Clear the password environment variable
$env:PGPASSWORD = ""

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")