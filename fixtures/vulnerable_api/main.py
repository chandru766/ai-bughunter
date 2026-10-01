from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
import jwt

app = FastAPI(title="Local Vulnerable Lab")
SECRET_KEY = "vulnerable_secret_for_local_testing"

class LoginData(BaseModel):
    username: str

@app.post("/auth/login")
def login(data: LoginData):
    token = jwt.encode({"sub": data.username, "role": "user"}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        scheme, token = authorization.split()
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/users/{user_id}/profile")
def get_user_profile(user_id: str, current_user: str = Depends(get_current_user)):
    # VULNERABILITY: BOLA - no ownership check
    return {"user_id": user_id, "data": f"Sensitive profile data for {user_id}", "accessed_by": current_user}

@app.get("/api/secure/users/{user_id}/profile")
def get_secure_profile(user_id: str, current_user: str = Depends(get_current_user)):
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"user_id": user_id, "data": f"Sensitive profile data for {user_id}", "accessed_by": current_user}
