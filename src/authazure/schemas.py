from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str
    id_token: str | None = None

class UserInfo(BaseModel):
    id: str
    name: str
    email: str | None = None

class AuthURL(BaseModel):
    auth_url: str