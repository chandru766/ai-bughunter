# AI-BugHunter Architecture & Workflows

This document outlines the core architecture, security boundaries, and data flows within AI-BugHunter. These diagrams represent the strict authorization controls that govern AI assistance during security research.

---

## 1. Core Architecture Overview

The system is separated into **Trusted Components** (where policies are enforced) and **Untrusted Components** (where external data and AI generation occurs).

```mermaid
flowchart TD
    subgraph TRUSTED_ZONE ["Trusted Zone (Strict Enforcement)"]
        Researcher(["Human Researcher"])
        UI["Dashboard Frontend"]
        API["FastAPI Backend"]
        Scope["Scope Validator"]
        Safety["Safety Policy Engine"]
        Exec["Safe Executor"]
        KillSwitch{"Global Kill Switch"}
    end

    subgraph ISOLATION_ZONE ["Data Isolation Zone"]
        Crypto["Authentication Bank"]
        DB[("SQLite Datastore")]
    end

    subgraph AI_ZONE ["AI Processing (Untrusted)"]
        RAG["RAG Context Builder"]
        LLM["AI Provider / LLM"]
    end

    subgraph TARGET_ZONE ["Untrusted Targets"]
        LocalLab(("Local Vulnerable Lab"))
    end

    Researcher -->|Configures & Approves| UI
    UI -->|JSON API| API
    API <-->|State & Auth| DB
    API <-->|Keys| Crypto
    
    API --> Scope
    Scope --> Safety
    Safety -->|Pending Approval| DB
    Safety -->|Approved| Exec
    
    Exec --> KillSwitch
    KillSwitch -->|Active| LocalLab
    LocalLab -->|HTTP Evidence| Exec
    
    Exec -->|Sanitized HTTP| RAG
    RAG -->|Enriched Context| LLM
    LLM -->|Analysis Hypothesis| API
```

---

## 2. Threat Modeling & Scope Validation

This flowchart details how AI-BugHunter prevents accidental Out-of-Bounds (OOB) requests or unauthorized scanning.

```mermaid
flowchart LR
    Start([Task Dispatch]) --> GetScope[Load Program Scope]
    GetScope --> CheckDomain{Domain Matches?}
    CheckDomain -- No --> Reject[Reject Request]
    CheckDomain -- Yes --> CheckPath{Path in Scope?}
    CheckPath -- No --> Reject
    CheckPath -- Yes --> CheckSchema{Schema Matches?}
    CheckSchema -- No --> Reject
    CheckSchema -- Yes --> Allowed([Validation Passed])
    
    style Reject fill:#ff4c4c,stroke:#333,stroke-width:2px,color:#fff
    style Allowed fill:#4caf50,stroke:#333,stroke-width:2px,color:#fff
```

---

## 3. Human-in-the-Loop Approval Workflow

AI-BugHunter strictly enforces that destructive or high-impact tests are explicitly authorized by a human researcher. AI agents cannot autonomously exploit systems.

```mermaid
sequenceDiagram
    participant AI as AI Planner
    participant Policy as Safety Policy
    participant DB as Database
    participant User as Researcher
    participant Exec as Safe Executor
    
    AI->>Policy: Propose BOLA Test (HIGH_IMPACT)
    Policy-->>DB: Save as APPROVAL_REQUIRED
    Note over AI, DB: Execution is immediately halted.
    
    User->>DB: Reviews pending Test Plan
    User->>DB: Clicks "Approve" (Status -> PLANNED)
    
    User->>Exec: Triggers Execution
    Exec->>DB: Verifies Status == PLANNED
    Exec-->>Target: Dispatches HTTP Payload
```

---

## 4. Evidence Handling & RAG Pipeline

When a test executes, the HTTP evidence is sanitized (secrets redacted) and combined with the internal Knowledge Base before being sent to the AI.

```mermaid
flowchart TD
    Raw[Raw HTTP Evidence] --> Redact[Secret Redaction]
    Redact --> Store[(Evidence Store)]
    
    Store --> FetchContext[Fetch RAG Context]
    KB[("Knowledge Base (Mock)")] --> FetchContext
    
    FetchContext --> SystemPrompt[Construct System Prompt]
    SystemPrompt --> Protect[Wrap with <<<DATA>>> tags]
    
    Protect --> LLM{LLM Inference}
    LLM -->|JSON Response| Parser[Structured Parser]
    
    Parser --> |Valid| NeedsVal([NEEDS_VALIDATION])
    Parser --> |Invalid| Error([Discard / Retry])
```

---

## 5. Finding Validation & Reporting Lifecycle

The AI acts as an assistant. It surfaces findings, but they are never considered valid until the human researcher confirms them.

```mermaid
stateDiagram-v2
    [*] --> NEEDS_VALIDATION : AI Detects Anomaly
    
    NEEDS_VALIDATION --> RESEARCHER_CONFIRMED : Researcher Approves
    NEEDS_VALIDATION --> FALSE_POSITIVE : Researcher Rejects
    
    RESEARCHER_CONFIRMED --> REPORT_GENERATED : Export Final Report
    FALSE_POSITIVE --> [*]
    REPORT_GENERATED --> [*]
```
