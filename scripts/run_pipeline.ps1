# scripts/run_pipeline.ps1
# Script thuc thi pipeline ELT HDB Singapore cho Windows Task Scheduler
# Chay hang ngay luc 08:15 sang.

$ErrorActionPreference = "Continue"

# Chuyen den thu muc goc cua du an
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Dam bao thu muc logs/scheduler ton tai (Khong xoa log cu)
$LogDir = Join-Path $ProjectRoot "logs\scheduler"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Now = Get-Date
$Timestamp = $Now.ToString("yyyyMMdd_HHmmss")
$LogFile = Join-Path $LogDir "run_$Timestamp.log"
$HistoryFile = Join-Path $LogDir "schedule_history.json"

Write-Output "==========================================================" | Tee-Object -FilePath $LogFile
Write-Output "HDB ELT SCHEDULED RUNNER - $Now" | Tee-Object -FilePath $LogFile -Append
Write-Output "Project Root: $ProjectRoot" | Tee-Object -FilePath $LogFile -Append
Write-Output "Log File: $LogFile" | Tee-Object -FilePath $LogFile -Append
Write-Output "==========================================================" | Tee-Object -FilePath $LogFile -Append

# Kiem tra va ghi nhan lan chay bi lo (Missed Runs Tracking)
$History = @()
$MissedRuns = @()

if (Test-Path $HistoryFile) {
    try {
        $RawJson = Get-Content $HistoryFile -Raw -Encoding UTF8
        if ($RawJson.Trim() -ne "") {
            $History = ConvertFrom-Json $RawJson
            if ($History -isnot [System.Array]) {
                $History = @($History)
            }
        }
    } catch {
        Write-Output "[WARN] Khong the doc file lich su: $_" | Tee-Object -FilePath $LogFile -Append
    }
}

if ($History.Count -gt 0) {
    $LastRun = $History[-1]
    $LastRunTime = [DateTime]::Parse($LastRun.start_time)
    $HoursSinceLastRun = ($Now - $LastRunTime).TotalHours

    # Neu khoang cach > 26 gio ke tu lan chay truoc, nghia la co it nhat mot lan chay 08:15 bi bo lo
    if ($HoursSinceLastRun -gt 26.0) {
        $EstimatedMissedDays = [Math]::Floor($HoursSinceLastRun / 24.0)
        $MissedMsg = "[CANH BAO LICH] Phat hien $EstimatedMissedDays lan chay bi lo giua $LastRunTime va $Now!"
        Write-Output $MissedMsg | Tee-Object -FilePath $LogFile -Append
        $MissedRuns += @{
            detected_at = $Now.ToString("o")
            hours_since_last_run = [Math]::Round($HoursSinceLastRun, 2)
            estimated_missed_count = $EstimatedMissedDays
            last_run_time = $LastRunTime.ToString("o")
        }
    } else {
        Write-Output "[LICH] Khoang cach tu lan chay truoc: $([Math]::Round($HoursSinceLastRun, 2)) gio (Dung lich trinh hang ngay)." | Tee-Object -FilePath $LogFile -Append
    }
} else {
    Write-Output "[LICH] Day la lan chay dau tien ghi nhan trong he thong Task Scheduler." | Tee-Object -FilePath $LogFile -Append
}

# Thiet lap moi truong Python
$env:PYTHONPATH = $ProjectRoot
Write-Output "[RUN] Bat dau thuc thi: python pipeline/run_pipeline.py..." | Tee-Object -FilePath $LogFile -Append

$StartTime = Get-Date

# Chay pipeline chinh va ghi vao log rieng biet
python pipeline/run_pipeline.py *>&1 | Tee-Object -FilePath $LogFile -Append
$ExitCode = $LASTEXITCODE

$EndTime = Get-Date
$DurationSec = [Math]::Round(($EndTime - $StartTime).TotalSeconds, 2)

if ($ExitCode -eq 0) {
    $Status = "SUCCESS"
    Write-Output ">>> PIPELINE THANH CONG (ExitCode: 0, Thoi gian: $DurationSec s)" | Tee-Object -FilePath $LogFile -Append
} else {
    $Status = "FAILED"
    Write-Output ">>> PIPELINE THAT BAI (ExitCode: $ExitCode, Thoi gian: $DurationSec s)" | Tee-Object -FilePath $LogFile -Append
}

# Ghi nhat ky vao file lich su tich luy (Khong bao gio xoa lich su cu)
$RunRecord = [PSCustomObject]@{
    run_id = [Guid]::NewGuid().ToString()
    start_time = $StartTime.ToString("o")
    end_time = $EndTime.ToString("o")
    duration_seconds = $DurationSec
    exit_code = $ExitCode
    status = $Status
    log_file = $LogFile
    missed_runs = $MissedRuns
}

$History += $RunRecord
$History | ConvertTo-Json -Depth 5 | Set-Content $HistoryFile -Encoding UTF8

Write-Output "[XONG] Da cap nhat lich su van hanh tai: $HistoryFile" | Tee-Object -FilePath $LogFile -Append
exit $ExitCode

