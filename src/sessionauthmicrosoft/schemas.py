
from pydantic import BaseModel
from uuid import UUID

class Token(BaseModel):
    """Token response received from Azure AD."""
    access_token: str
    token_type: str
    id_token: str | None = None

class UserInfo(BaseModel):
    """Raw user information fetched from Microsoft Graph."""
    id: str
    name: str
    email: str | None = None

class AuthURL(BaseModel):
    """Schema for sending the login URL to the frontend."""
    auth_url: str

class UserManagementOut(BaseModel):
    """Defines the user profile data returned by the universal /me endpoint."""
    id: UUID
    id_user: str
    id_team: UUID
    email: str
    account_type: str

    class Config:
        orm_mode = True

class StatusResponse(BaseModel):
    """Generic schema for simple status responses."""
    status: str
    message: str