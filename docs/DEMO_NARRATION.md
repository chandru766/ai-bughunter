# Demo Narration Script

**[00:00]** 
"Hello. Today I want to demonstrate AI-BugHunter. What you're seeing is an AI-assisted security research workflow—rather than an autonomous hacking system. The fundamental principle here is that humans retain absolute control over all critical decisions, and the AI acts purely as an analytical assistant."

**[00:15]** 
"As we look at the architecture, you'll see a hard boundary between trusted application components and untrusted external data. The LLM is strictly separated from the execution engine."

**[00:30]**
"Let's start the demo. First, we define our scope. The `ScopeValidator` enforces that all operations are restricted to our local, authorized vulnerable lab running on `127.0.0.1`. The platform will abort instantly if we try to scan an external target."

**[00:50]**
"Next, we create a test plan. In this case, we are testing for Prompt Injection. Because this is an invasive test, it is automatically categorized as `HIGH_IMPACT`."

**[01:10]**
"Notice that execution halts here. The test is parked in an `APPROVAL_REQUIRED` state. The AI cannot bypass this. A human researcher must explicitly approve the test plan before the `SafeExecutor` allows the outbound HTTP request."

**[01:25]**
"With human approval granted, we execute against the local mock lab. The `SafeExecutor` binds our authentication context, but importantly, it scrubs the keys from the HTTP evidence. We see `[REDACTED]` where our API keys would be, ensuring we never leak secrets to the LLM."

**[01:45]**
"The HTTP evidence is collected and passed to the AI. Using Retrieval-Augmented Generation (RAG), the AI maps the hostile response against our trusted internal policy rules, identifying a potential structural flaw in the response."

**[02:05]**
"The AI produces a structured JSON hypothesis. But crucially, the finding defaults to the `NEEDS_VALIDATION` state. The AI does not have the authority to confirm a vulnerability on its own."

**[02:20]**
"I, as the researcher, review the AI's hypothesis against the raw HTTP evidence. I agree with the assessment, so I manually transition the finding to `RESEARCHER_CONFIRMED`. Every step of this is tracked in the immutable audit log."

**[02:35]**
"Finally, we generate the final security report. This Markdown artifact only contains findings that a human has explicitly validated."

**[02:50]**
"AI-BugHunter accelerates the heavy lifting of evidence analysis while structurally enforcing safety, scope, and human authority. Thank you for watching."
