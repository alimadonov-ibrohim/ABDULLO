$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "[~] Bot to'xtatilmoqda..."
& (Join-Path $Root "stop_bot.ps1")

Start-Sleep -Seconds 1

Write-Host "[~] Bot qayta ishga tushirilmoqda..."
& (Join-Path $Root "start_bot.ps1")
