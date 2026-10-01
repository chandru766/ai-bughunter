from pydantic import BaseModel

class AuthContextCreate(BaseModel):
    program_id: int
    name: str
    account_label: str
    auth_type: str
    secret: str

class AuthContextResponse(BaseModel):
    id: int
    name: str
    account_label: str
    auth_type: str
    secret: str
    enabled: bool

    class Config:
        from_attributes = True
