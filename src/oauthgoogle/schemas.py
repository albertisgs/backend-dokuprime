from pydantic import BaseModel

class Token(BaseModel):
    """
    Represents the token response from Google.
    """
    access_token: str
    token_type: str
    id_token: str | None = None

class UserInfo(BaseModel):
    """
    Represents the user information we want to expose.
    """
    id: str
    name: str
    email: str | None = None
    picture: str | None = None
    id_role: str | None = None
    account_type: str | None = None

class AuthURL(BaseModel):
    """
    Represents the authentication URL to be sent to the frontend.
    """
    auth_url: str
