# Demo Privacy Checklist

Before taking any screenshots for the portfolio demonstration or uploading any demo output artifacts, strictly verify that none of the following sensitive items are visible. The demo is meant to be run entirely on a local `127.0.0.1` lab, but accidents happen during screen recording.

## Verification Checklist

- [ ] **No JWTs**: JSON Web Tokens must be scrubbed or `[REDACTED]` from all HTTP headers or raw payload views.
- [ ] **No Authorization headers**: Any `Authorization: Bearer <token>` or `Basic <base64>` must show as `[REDACTED]`.
- [ ] **No API Keys**: Ensure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` are not visible in terminal histories or environment variable outputs.
- [ ] **No Passwords**: Do not display mock user passwords; if necessary, ensure they are dummy values like `hunter2`.
- [ ] **No Cookies**: Session cookies in HTTP headers must be stripped or obfuscated.
- [ ] **No Session Tokens**: Any state-tracking tokens must be obscured.
- [ ] **No Encryption Keys**: The `Fernet` key used by the `AuthBank` MUST NOT be visible anywhere in the configuration windows.
- [ ] **No Personal Information**: Hostnames must be strictly `127.0.0.1` or `localhost`. Do not expose real client names or target environments.

## How to Handle Sensitive Data
Always use the exact string `[REDACTED]` where applicable. The platform's `AuthBank` redaction layer does this automatically for outgoing `SafeExecutor` logs, but you must manually verify this behavior before recording the screen.
