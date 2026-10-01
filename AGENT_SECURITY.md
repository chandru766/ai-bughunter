# Phase 21: AI Agent Security & Tool-Calling Framework

## Overview
The Phase 21 AI Agent Security testing framework introduces a robust, highly structured environment for verifying the security, authorization, and boundaries of AI agents that can utilize tools. It ensures that any agent deployed within the AI-BugHunter ecosystem adheres to strict safety boundaries. 

The core philosophy of this framework is that **the LLM's output is untrusted and never constitutes an authorization decision**. All tool invocations must pass through a strict backend verification gate before execution.

## Trust Boundaries
The following critical security properties are enforced:
- **LLM Output ≠ Authorization**: Just because the LLM decides to call `delete_user` does not mean it is authorized to do so.
- **Backend Enforced Identities**: The system uses `SYSTEM_IDENTITY`, `USER_IDENTITY`, and `AGENT_IDENTITY` separately. All authorization relies exclusively on the verified `USER_IDENTITY` and `AGENT_IDENTITY`, not on the text provided in the prompt.
- **Explicit Permissions**: Agent tools operate on a default-deny model. Without an explicit `ToolPermission` of `ALLOWED`, the tool execution is blocked.

## Architecture

### 1. Agent Architecture
- **AIAgent**: Represents a tool-capable AI agent tied to a specific `Program` and `AIApplication`.
- **AgentTool**: Represents a discrete function the agent can invoke (e.g., `get_user`, `delete_order`). Every tool has a `ToolRiskLevel` (`READ_ONLY`, `LOW_IMPACT`, `HIGH_IMPACT`, `BLOCKED`).
- **ToolPermission**: Maps an `AIAgent` and a `Tool` to a specific `user_identity` and determines if the execution state is `ALLOWED`, `APPROVAL_REQUIRED`, or `BLOCKED`.

### 2. ToolExecutionGate
The `ToolExecutionGate` is the central safety choke point. Before any tool executes, it verifies:
1. The global Kill Switch is inactive.
2. The Agent is `ACTIVE`.
3. The Tool exists and is enabled.
4. The Agent has an explicit `ToolPermission` for the verified user identity.
5. If the tool is `HIGH_IMPACT` or the permission state is `APPROVAL_REQUIRED`, execution is blocked pending explicit human approval.
6. The JSON payload matches the tool's strict `schema_def`.
7. The agent has not exceeded its Action Budget or entered an execution loop.

### 3. Action Budgets and Loop Detection
To prevent agents from spinning infinitely or exhausting resources:
- The framework tracks tool call history per agent.
- If the agent calls the same tool repeatedly (e.g., 3 consecutive identical calls), a loop is detected and execution is paused with an `AGENT_LOOP_DETECTED` event.
- If the agent exceeds a global hard limit (`MAX_CALLS_PER_AGENT`), it is blocked.

### 4. Tool Output Sanitization
Tool results are untrusted and must be sanitized before they are returned to the LLM to prevent prompt injection or secret leakage:
- Values matching common secret patterns (e.g., AWS keys, API tokens) are `[REDACTED]`.
- Output strings exceeding 1000 characters are safely `[TRUNCATED]` to prevent context-window flooding.

### 5. Local Agent Lab (127.0.0.1:9200)
A deliberately vulnerable local fixture is provided for E2E testing without external exposure:
- It includes mock endpoints (`/api/chat`, `/api/tools/execute`) and synthetic data (`SYNTHETIC_USER_DATA`, `SYNTHETIC_ORDERS`).
- A `delete_user` tool simulates privilege escalation paths.
- A `search_documents` tool simulates Indirect Prompt Injection (returning malicious payloads to the agent).
- A `create_ticket` tool simulates Tool Output Injection.
- **CRITICAL**: No external connectivity is configured. Synthetic secrets (`AGENT_TEST_SECRET_123`) are used exclusively.

## Security Limitations
- **Dynamic Reasoning Analysis**: The framework intercepts execution *before* a tool runs, but complex, semantic multi-step attacks (e.g., splitting a payload across two valid tool calls) require the overarching `AIPipeline` semantic analyzer to detect malicious intent.
- **Manual Approvals**: High-impact actions require out-of-band human approvals. There is currently no UI for a researcher to approve an in-flight tool call; they are outright blocked with an `APPROVAL_REQUESTED` log event in this simulation.
- **Mock Tool Realism**: The Local Agent Lab simulates backend authorization via hardcoded Python logic (`if req.user_identity != uid:`). In a real deployment, these tools would be integrated directly with the platform's RBAC engine.
