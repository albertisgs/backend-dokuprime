from pydantic import BaseModel
from uuid import UUID

class Token(BaseModel):
    """
    Represents the token response received directly from Google
    after exchanging the authorization code.
    """
    access_token: str
    token_type: str
    id_token: str | None = None

class UserInfo(BaseModel):
    """
    Represents the raw user information fetched from Google's
    /userinfo endpoint. This is used internally.
    """
    id: str
    name: str
    email: str | None = None
    picture: str | None = None

class AuthURL(BaseModel):
    """
    A simple schema for sending the generated Google login URL
    to the frontend.
    """
    auth_url: str

class UserManagementOut(BaseModel):
    """
    Defines the user profile data returned by the /me endpoint.
    This structure directly reflects the columns in your
    `user_management` table.
    """
    id: UUID
    id_user: str
    id_role: UUID
    email: str
    account_type: str

    class Config:
        # This allows the model to be created from database objects
        orm_mode = True

class StatusResponse(BaseModel):
    """
    A generic schema for simple status responses, used for
    endpoints like /verify-me or /logout.
    """
    status: str
    message: str