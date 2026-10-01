$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "AI-BUGHUNTER AUTOMATED DEMO RECORDING"
Write-Host "========================================"
Write-Host ""

Write-Host "Checking for Python..."
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ABORT: Python is not installed or not in PATH."
    exit 1
}

Write-Host "Checking for Playwright dependency..."
try {
    python -c "import playwright" *>$null
} catch {
    # Ignore
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "Playwright is not installed."
    Write-Host "Adding demo dependencies..."
    pip install playwright
    python -m playwright install chromium
}

Write-Host "Starting frontend server..."
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "C:\kali-shared\ai-bughunter\frontend"
    python -m http.server 8080
}

Write-Host "Starting recording..."
try {
    python scripts/demo/record_demo.py
    $recordResult = $LASTEXITCODE
} finally {
    Write-Host "Cleaning up frontend server..."
    Stop-Job -Job $frontendJob
    Remove-Job -Job $frontendJob
}

if ($recordResult -eq 0) {
    Write-Host "========================================"
    Write-Host "DEMO RECORDING SUCCESSFUL"
    Write-Host "Output: demo/recording/video/ai-bughunter-demo.webm"
    Write-Host "========================================"
} else {
    Write-Host "========================================"
    Write-Host "DEMO RECORDING ABORTED"
    Write-Host "========================================"
    exit 1
}
