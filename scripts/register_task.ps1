# scripts/register_task.ps1
# Dang ky Task Scheduler cho Windows de thuc thi pipeline hang ngay vao luc 08:15 sang.

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $ProjectRoot "scripts\run_pipeline.ps1"
$TaskName = "HDB_ELT_Daily_Run"

Write-Host "Dang ky Windows Task Scheduler..."
Write-Host "Ten tac vu: $TaskName"
Write-Host "File thuc thi: $ScriptPath"
Write-Host "Lich trinh: Hang ngay luc 08:15 AM"

$ActionCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""

# Goi schtasks de tao hoac cap nhat tac vu
& schtasks.exe /create /tn $TaskName /tr $ActionCmd /sc DAILY /st 08:15 /f

if ($LASTEXITCODE -eq 0) {
    Write-Host ">>> DANG KY THANH CONG TAC VU $TaskName" -ForegroundColor Green
    Write-Host "`nThong tin chi tiet tac vu:"
    & schtasks.exe /query /tn $TaskName /fo LIST /v
} else {
    Write-Error "Loi khi dang ky Windows Task Scheduler."
}

