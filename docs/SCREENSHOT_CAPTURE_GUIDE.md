# Screenshot Capture Guide

This guide explains how to manually capture the required portfolio screenshots. Do NOT use automated browser capturing tools for this demo; you must manually step through the application state or use the CLI outputs to properly frame the security boundaries.

**Important**: Before proceeding, verify you have read `DEMO_PRIVACY_CHECKLIST.md`.

## Screenshot 01: 01-dashboard.png
- **Action**: Open the frontend (`http://localhost:8080` if serving `index.html`) in your browser.
- **Capture**: Show dashboard with project overview. Ensure no real client data is mocked in the UI.

## Screenshot 02: 02-program.png
- **Action**: Run the demo script or navigate to the Program Management view.
- **Capture**: Show local program. Ensure the URL field explicitly reads `http://127.0.0.1:9100`.

## Screenshot 03: 03-test-plan.png
- **Action**: Open `demo/output/01_test_plan.json` in a code editor with syntax highlighting, or show the terminal output where the plan is created.
- **Capture**: Show test plan and target. Make sure `safety_level` or similar fields are visible indicating `HIGH_IMPACT`.

## Screenshot 04: 04-human-approval.png
- **Action**: In the terminal or UI, capture the exact moment the script prints `Approving Test Plan...` and the API responds with `{"status": "APPROVED"}`.
- **Capture**: Show APPROVED status. Frame it to highlight that the step required a distinct interaction.

## Screenshot 05: 05-execution.png
- **Action**: Open `demo/output/03_execution.json` in your editor.
- **Capture**: Show execution result. Highlight the `evidence` field, explicitly capturing the `Bearer [REDACTED]` string to prove AuthBank token sanitization is working.

## Screenshot 06: 06-ai-analysis.png
- **Action**: Continue looking at `demo/output/03_execution.json` under the `ai_analysis` block.
- **Capture**: Show AI analysis. The structured JSON schema, confidence ratings, and citations should be highly visible.

## Screenshot 07: 07-needs-validation.png
- **Action**: Scroll down in the terminal output or UI to show the `NEEDS_VALIDATION` state assertion.
- **Capture**: Show NEEDS_VALIDATION.

## Screenshot 08: 08-researcher-validation.png
- **Action**: Open `demo/output/05_validation.json` in your editor or show the terminal step where human validation is triggered.
- **Capture**: Show researcher validation. Capture the `decision: CONFIRM` and the status changing to `RESEARCHER_CONFIRMED`.

## Screenshot 09: 09-final-report.png
- **Action**: Open `demo/output/ai-bughunter-demo-report.md` in a Markdown viewer.
- **Capture**: Show final report. Ensure the formatting is clean and professional.

*(Note: All screenshots must be captured manually by the presenter. The platform does not natively automate headless browser capturing as it is an orchestration layer, not an E2E testing tool).*
