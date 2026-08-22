$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $Root "bot.pid"
$LogDir = Join-Path $Root "logs"
$StdOut = Join-Path $LogDir "stdout.log"

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# Allaqachon ishlab turganini tekshirish
if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
        Write-Host "[!] Bot allaqachon ishlayapti (PID $oldPid). Qayta ishga tushirish uchun: reload_bot.ps1"
        exit 1
    }
}

$PyExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $PyExe)) { $PyExe = "python" }

$proc = Start-Process -FilePath $PyExe `
    -ArgumentList "`"$Root\bot.py`"" `
    -WorkingDirectory $Root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $StdOut `
    -RedirectStandardError (Join-Path $LogDir "stderr.log") `
    -PassThru

Set-Content -Path $PidFile -Value $proc.Id
Write-Host "[+] Bot fon rejimida ishga tushdi. PID: $($proc.Id)"
Write-Host "    Loglar : logs\bot.log, logs\bot_err.log"
Write-Host "    To'xtatish: stop_bot.ps1 | Qayta yuklash: reload_bot.ps1"
