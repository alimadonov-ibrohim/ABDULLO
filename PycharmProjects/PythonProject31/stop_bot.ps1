$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $Root "bot.pid"

$stopped = $false

if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile
    if ($oldPid) {
        $proc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($proc -and $proc.ProcessName -match "python") {
            Stop-Process -Id $oldPid -Force
            Start-Sleep -Milliseconds 500
            Write-Host "[+] Bot to'xtatildi (PID $oldPid)"
            $stopped = $true
        }
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

if (-not $stopped) {
    # PID fayli yo'q/yaroqsiz bo'lsa — bot.py nomi bilan python jarayonlarini topamiz
    $found = Get-CimInstance Win32_Process |
        Where-Object { $_.Name -match "^python" -and $_.CommandLine -match "bot\.py" }
    if ($found) {
        foreach ($p in $found) {
            Stop-Process -Id $p.ProcessId -Force
            Write-Host "[+] Topildi va to'xtatildi (PID $($p.ProcessId))"
        }
    } else {
        Write-Host "[!] Ishlayotgan bot topilmadi."
    }
}
