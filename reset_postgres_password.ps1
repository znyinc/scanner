# Reset PostgreSQL Password Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Password Reset" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This script will help you reset the PostgreSQL postgres user password." -ForegroundColor Yellow
Write-Host "You'll need administrator privileges for this operation." -ForegroundColor Yellow
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "ERROR: This script needs to be run as Administrator." -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Running as Administrator ✓" -ForegroundColor Green
Write-Host ""

# Step 1: Stop PostgreSQL service
Write-Host "Step 1: Stopping PostgreSQL service..." -ForegroundColor Green
try {
    Stop-Service -Name "postgresql-x64-17" -Force
    Write-Host "PostgreSQL service stopped ✓" -ForegroundColor Green
}
catch {
    Write-Host "Warning: Could not stop PostgreSQL service: $_" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Backup and modify pg_hba.conf
Write-Host "Step 2: Modifying PostgreSQL authentication..." -ForegroundColor Green

$pgHbaPath = "C:\Program Files\PostgreSQL\17\data\pg_hba.conf"
$pgHbaBackup = "C:\Program Files\PostgreSQL\17\data\pg_hba.conf.backup"

if (Test-Path $pgHbaPath) {
    # Create backup
    Copy-Item $pgHbaPath $pgHbaBackup -Force
    Write-Host "Created backup: pg_hba.conf.backup ✓" -ForegroundColor Green
    
    # Read and modify the file
    $content = Get-Content $pgHbaPath
    $newContent = @()
    
    foreach ($line in $content) {
        if ($line -match "^host\s+all\s+all\s+127\.0\.0\.1/32\s+scram-sha-256") {
            $newContent += $line -replace "scram-sha-256", "trust"
            Write-Host "Modified authentication method to 'trust' ✓" -ForegroundColor Green
        } elseif ($line -match "^host\s+all\s+all\s+::1/128\s+scram-sha-256") {
            $newContent += $line -replace "scram-sha-256", "trust"
        } else {
            $newContent += $line
        }
    }
    
    # Write the modified content
    $newContent | Set-Content $pgHbaPath -Encoding UTF8
    Write-Host "Updated pg_hba.conf ✓" -ForegroundColor Green
} else {
    Write-Host "ERROR: Could not find pg_hba.conf at $pgHbaPath" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Start PostgreSQL service
Write-Host "Step 3: Starting PostgreSQL service..." -ForegroundColor Green
try {
    Start-Service -Name "postgresql-x64-17"
    Start-Sleep -Seconds 3
    Write-Host "PostgreSQL service started ✓" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Could not start PostgreSQL service: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Reset password
Write-Host "Step 4: Resetting postgres password..." -ForegroundColor Green

$newPassword = "admin123"
$env:PGPASSWORD = ""

try {
    $result = psql -U postgres -d postgres -c "ALTER USER postgres PASSWORD '$newPassword';" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Password reset successfully ✓" -ForegroundColor Green
        Write-Host "New postgres password: $newPassword" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: Failed to reset password: $result" -ForegroundColor Red
    }
} catch {
    Write-Host "ERROR: Could not connect to reset password: $_" -ForegroundColor Red
}

Write-Host ""

# Step 5: Restore authentication
Write-Host "Step 5: Restoring authentication settings..." -ForegroundColor Green

try {
    Stop-Service -Name "postgresql-x64-17" -Force
    
    # Restore the backup
    Copy-Item $pgHbaBackup $pgHbaPath -Force
    Write-Host "Restored original pg_hba.conf ✓" -ForegroundColor Green
    
    Start-Service -Name "postgresql-x64-17"
    Start-Sleep -Seconds 3
    Write-Host "PostgreSQL service restarted ✓" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not restore authentication settings: $_" -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Test new password
Write-Host "Step 6: Testing new password..." -ForegroundColor Green

$env:PGPASSWORD = $newPassword
$testResult = psql -U postgres -d postgres -c "SELECT 'Password reset successful!' as status;" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS! Password reset complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "New postgres password: $newPassword" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now run the setup script again:" -ForegroundColor Yellow
    Write-Host ".\setup_postgres_interactive.ps1" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "ERROR: Password test failed: $testResult" -ForegroundColor Red
    Write-Host "You may need to manually check the PostgreSQL configuration." -ForegroundColor Yellow
}

$env:PGPASSWORD = ""

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")