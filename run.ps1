# CloudOptima One-Click Startup Script for PowerShell
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Starting CloudOptima Multi-Cloud FinOps Platform       " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "`n[1/2] Opening CloudOptima Dashboard in your default browser..." -ForegroundColor Green
Start-Process "http://localhost:8000/"

Write-Host "[2/2] Launching CloudOptima Server on port 8000..." -ForegroundColor Green
Write-Host "Press Ctrl+C anytime to stop the server.`n" -ForegroundColor DarkGray

python run.py
