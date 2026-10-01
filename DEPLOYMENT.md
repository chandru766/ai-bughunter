# DEPLOYMENT GUIDE: AI-BugHunter

## Requirements
- Python 3.10+
- Node.js (for frontend development if running separately)
- SQLite (Development) or PostgreSQL (Production)
- Reverse proxy (e.g., Nginx) for TLS termination in production

## Environment Variables
Copy `.env.example` to `.env` and fill in the required values.
- `APP_ENV`: Set to `production` for production environments.
- `AUTH_BANK_ENCRYPTION_KEY`: **CRITICAL**. Must be a fixed url-safe base64 key in production. If lost, all stored secrets are irrecoverable.
- `CORS_ORIGINS`: Set to your production frontend URL (e.g., `https://bughunter.internal`). Do not use `*`.

## Startup

### Backend
1. `python -m pip install -r backend/requirements.txt`
2. `cd backend`
3. `uvicorn main:app --host 127.0.0.1 --port 8000`

### Frontend
1. Serve the `frontend/` directory using any web server.
2. In production, configure Nginx to serve `frontend/` and reverse-proxy `/api` to the backend.

## Security Configuration
- **Authentication**: Currently, the dashboard assumes an isolated, trusted network environment (e.g., accessed via VPN or localhost). Do NOT expose the dashboard to the public internet without an authenticating reverse proxy (like Authelia or OAuth2 Proxy).
- **Kill Switch**: The system starts with the Kill Switch INACTIVE. It can be toggled via the dashboard.
- **Backups**: Run regular backups of `bughunter.db`. The DB contains encrypted secrets; they remain safe at rest as long as `AUTH_BANK_ENCRYPTION_KEY` is not compromised.
- **Incident Response**: If you suspect a rogue AI test is running, immediately hit the Kill Switch on the dashboard, which halts all outbound testing capabilities.

## Safe Shutdown
Standard `SIGTERM` to the backend process allows active requests to complete gracefully.
