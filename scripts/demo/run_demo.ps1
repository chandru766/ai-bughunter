# AI-BugHunter Automated Local Demo
# This script orchestrates the Python demo application to ensure 
# safe, reproducible local evaluations of the platform workflow.

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "AI-BUGHUNTER LOCAL DEMO WRAPPER"
Write-Host "========================================"
Write-Host ""

# Ensure backend bytecode is compiled as part of the readiness check
Write-Host "Pre-compiling backend..."
python -m compileall backend | Out-Null
Write-Host "Done."
Write-Host ""

# Run the python-based demo orchestration script
python scripts/demo/run_demo.py
