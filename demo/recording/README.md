# AI-BugHunter Demo Recording

This directory contains the automated portfolio demonstration recording for AI-BugHunter.

## Artifacts
- **Video**: `video/ai-bughunter-demo.webm` (Playwright Chromium Recording)
- **Screenshots**: `screenshots/`
- **Metadata**: `metadata/demo-metadata.json`

## Safety Boundaries Enforced
- Target locked to `127.0.0.1`.
- Human validation explicitly requested.
- Redaction active for all tokens.
- No external scans initiated.

## Reproduction
To regenerate this recording, execute:
```powershell
.\scripts\demo\record_demo.ps1
```
Requires Python and Playwright.
