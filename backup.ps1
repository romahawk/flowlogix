# backup.ps1 — Backup SQLite DB with timestamp
# Run:  .\backup.ps1

# Path to your live DB
$DbPath = "instance\supply_tracker.db"

# Backup directory
$BackupDir = "backups"

# Make sure DB exists
if (-Not (Test-Path $DbPath)) {
    Write-Host "❌ Database not found at $DbPath"
    exit 1
}

# Ensure backups folder exists
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# Create timestamp
$ts = Get-Date -Format "yyyyMMdd_HHmm"

# Build destination path
$BackupFile = Join-Path $BackupDir ("supply_tracker_$ts.db")

# Copy DB
Copy-Item $DbPath $BackupFile -Force

Write-Host "✅ Backup created: $BackupFile"
