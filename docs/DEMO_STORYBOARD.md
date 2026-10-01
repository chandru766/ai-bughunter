# Demo Storyboard

**Total Estimated Duration**: ~3 minutes

## 00:00–00:15 | Project introduction
- **Visual**: Show the AI-BugHunter GitHub README overview or the main web dashboard.
- **Action**: Briefly introduce the platform as an "AI-assisted security research workflow, not an autonomous hacking system."

## 00:15–00:30 | Architecture/security boundary
- **Visual**: Scroll to the architecture diagram showing the "Trusted vs Untrusted" boundary.
- **Action**: Point out that the LLM is untrusted and humans make all final decisions.

## 00:30–00:50 | Create/select local program
- **Visual**: Open the terminal or UI and run the start of `run_demo.ps1`.
- **Action**: Show the safety validation step confirming the target is restricted to `127.0.0.1`.

## 00:50–01:10 | Create test plan
- **Visual**: Show the SQLite/JSON payload for the `HIGH_IMPACT` Prompt Injection test plan.
- **Action**: Highlight the strict scope enforcement and safety categorization.

## 01:10–01:25 | Human approval
- **Visual**: Focus on the `APPROVAL_REQUIRED` status blocking execution.
- **Action**: Demonstrate the manual human interaction required to unblock the execution.

## 01:25–01:45 | Execute against local vulnerable lab
- **Visual**: The `SafeExecutor` terminal logs firing the HTTP request to the local `9100` port.
- **Action**: Emphasize how `AuthBank` redacts keys (showing `[REDACTED]`) before the evidence is stored.

## 01:45–02:05 | Evidence + AI/RAG analysis
- **Visual**: Show the `03_execution.json` output alongside the AI's structured analysis response.
- **Action**: Explain that the AI maps hostile responses to internal RAG rules to form a hypothesis.

## 02:05–02:20 | Finding reaches NEEDS_VALIDATION
- **Visual**: The UI/terminal explicitly showing the finding parked in `NEEDS_VALIDATION`.
- **Action**: State clearly: "The AI cannot independently confirm vulnerabilities."

## 02:20–02:35 | Researcher validates finding
- **Visual**: Command or UI simulating the researcher marking the finding as `RESEARCHER_CONFIRMED`.
- **Action**: Final human authorization is granted based on the evidence collected.

## 02:35–02:50 | Generate report
- **Visual**: Open `ai-bughunter-demo-report.md`.
- **Action**: Scroll through the final, clean, human-validated markdown report.

## 02:50–03:00 | Show GitHub/project architecture
- **Visual**: Return to the repository view.
- **Action**: Wrap up by reiterating the security-first, human-in-the-loop philosophy.
