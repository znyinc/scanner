# Simple PostgreSQL Password Reset Script
Write-Host "PostgreSQL Password Reset" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "ERROR: Run as Administrator required" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Step 1: Stopping PostgreSQL..." -ForegroundColor Green
Stop-Service -Name "postgresql-x64-17" -Force -ErrorAction SilentlyContinue

Write-Host "Step 2: Modifying authentication..." -ForegroundColor Green
$pgHbaPath = "C:\Program Files\PostgreSQL\17\data\pg_hba.conf"
$backupPath = $pgHbaPath + ".backup"

if (Test-Path $pgHbaPath) {
    Copy-Item $pgHbaPath $backupPath -Force
    $content = Get-Content $pgHbaPath
    $content = $content -replace "scram-sha-256", "trust"
    $content | Set-Content $pgHbaPath
    Write-Host "Authentication modified" -ForegroundColor Green
}

Write-Host "Step 3: Starting PostgreSQL..." -ForegroundColor Green
Start-Service -Name "postgresql-x64-17"
Start-Sleep 3

Write-Host "Step 4: Resetting password..." -ForegroundColor Green
$env:PGPASSWORD = ""
psql -U postgres -d postgres -c "ALTER USER postgres PASSWORD 'admin123';"

Write-Host "Step 5: Restoring authentication..." -ForegroundColor Green
Stop-Service -Name "postgresql-x64-17" -Force
Copy-Item $backupPath $pgHbaPath -Force
Start-Service -Name "postgresql-x64-17"
Start-Sleep 3

Write-Host "Step 6: Testing..." -ForegroundColor Green
$env:PGPASSWORD = "admin123"
$result = psql -U postgres -d postgres -c "SELECT 'Success!' as status;"

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS! New password: admin123" -ForegroundColor Green
} else {
    Write-Host "FAILED! Check manually" -ForegroundColor Red
}

$env:PGPASSWORD = ""
Read-Host "Press Enter to continue"