# AI-BugHunter Installation

## 1. Requirements
- Python 3.10+
- Git
- SQLite (built-in with Python)

## 2. Clone/setup
Clone the repository:
```bash
git clone https://github.com/yourusername/ai-bughunter.git
cd ai-bughunter
```

## 3. Python environment
Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

## 4. Dependencies
Install the required Python packages from the backend directory:
```bash
cd backend
pip install -r requirements.txt
```

## 5. Environment variables
No external API keys are required to run the local mock demo.
Optional variables (if using real AI providers instead of mocks):
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
```

## 6. Database
The SQLite database will automatically initialize when you start the backend server (`bughunter.db` will be created).

## 7. Backend
Start the FastAPI backend server (from the `backend` directory):
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

## 8. Frontend
The frontend is a vanilla HTML/JS single-page application.
You can open `frontend/index.html` directly in your browser or serve it locally:
```bash
cd frontend
python -m http.server 8080
```

## 9. Local vulnerable lab
The platform ships with a safe, mocked local vulnerable lab for testing.
Start it in a new terminal window:
```bash
cd backend
python local_ai_lab.py
```
*(The lab will run on `127.0.0.1:9100`)*

## 10. Tests
The test suite utilizes `pytest`. Note: there are 6 expected fixture teardown warnings/failures due to async SQLite limitations in testing, but the core suite will pass.
```bash
python -m pytest tests/unit -v
```

## 11. Troubleshooting
- **Database Schema Errors**: If you encounter `OperationalError` regarding missing columns, delete `backend/bughunter.db` and restart the backend to recreate the schema.
- **Port Conflicts**: Ensure ports `8000` (backend) and `9100` (local lab) are not in use.
