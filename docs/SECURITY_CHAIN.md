```mermaid
flowchart TD
    Scope --> Safety
    Safety --> Approval[Human Approval]
    Approval --> SafeExec[Safe Execution]
    SafeExec --> Evidence
    Evidence --> AI[AI Analysis]
    AI --> NeedsVal[NEEDS_VALIDATION]
    NeedsVal --> HumanVal[Human Validation]
    HumanVal --> Report
```
