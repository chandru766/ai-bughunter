# AI-BugHunter Local Demo

## Purpose
This directory contains the automated local demonstration script for the AI-BugHunter platform. The script safely walks through the complete lifecycle (planning, approval, execution, AI analysis, human validation, reporting) entirely within a closed, local mock environment.

## Prerequisites
- Python 3.10+
- The `ai-bughunter` backend must be running.
- The `local_ai_lab` must be running.

## How to Start Backend
Open a terminal and run:
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## How to Start Local Lab
Open a second terminal and run:
```bash
cd backend
python local_ai_lab.py
```
*(This mock vulnerable lab will listen on `127.0.0.1:9100`)*

## How to Run the Demo
Open a third terminal and run the PowerShell script:
```powershell
.\scripts\demo\run_demo.ps1
```

## Expected Workflow
The script will perform exactly 10 automated steps:
1. Check backend health.
2. Check local lab health.
3. Validate that the target is strictly `127.0.0.1` or `localhost`.
4. Select/create the local demo program.
5. Create a `HIGH_IMPACT` test plan targeting the lab.
6. Simulate human approval to unblock the execution.
7. Instruct the `SafeExecutor` to dispatch the HTTP test.
8. Validate the AI pipeline returns a structured finding in `NEEDS_VALIDATION`.
9. Simulate researcher validation transitioning it to `RESEARCHER_CONFIRMED`.
10. Generate the final markdown report.

## Generated Artifacts
Upon completion, the script saves its sanitized evidence and results to:
- `demo/output/01_test_plan.json`
- `demo/output/02_approval.json`
- `demo/output/03_execution.json`
- `demo/output/04_needs_validation.json` (Currently skipping in the Python version, wait I will add it)
- `demo/output/05_validation.json`
- `demo/output/ai-bughunter-demo-report.md`
- `demo/output/demo-summary.md`

All execution steps and assertions are strictly recorded in `demo/logs/demo.log`.

## Safety Restrictions
This demo is hardcoded to actively **ABORT** if the target is anything other than `127.0.0.1` or `localhost`. The `SafeExecutor` scope validation checks also prevent arbitrary external domain access. Unrestricted scanning is strictly forbidden by the architecture.

## Portfolio Demo
This directory also supports capturing artifacts for a 2–3 minute professional portfolio demonstration.

**Prerequisites:** Backend and local lab running, environment configured.
**Startup:** Use the command above to launch the wrapper script.
**Demo Command:** `.\scripts\demo\run_demo.ps1`
**Workflow:** The 10-step automation safely runs the exact sequence from planning to reporting.
**Screenshots:** Follow the `docs/SCREENSHOT_CAPTURE_GUIDE.md` to properly frame the UI and logs to highlight safety borders.
**Generated Artifacts:** Refer to `demo/output/README.md` for details on the sanitized outputs.
**Safety Boundary:** The target checks explicitly limit execution to the local mock environment, ensuring zero external bleed.
