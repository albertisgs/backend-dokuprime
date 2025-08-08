from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .handler import GoogleOAuthHandler
from .schemas import UserInfo

# This scheme is used to extract the token from the "Authorization: Bearer <token>" header.
# The tokenUrl is not directly used in the auth code flow but is required by FastAPI's security utilities.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authgoogle/token")

def get_google_oauth_handler() -> GoogleOAuthHandler:
    """
    Dependency to get an instance of the GoogleOAuthHandler.
    """
    return GoogleOAuthHandler()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    handler: GoogleOAuthHandler = Depends(get_google_oauth_handler)
) -> UserInfo:
    """
    Dependency to get the current user from the provided access token.
    It fetches user information from Google.
    """
    return await handler.get_user_info(token)

async def verify_token(
    token: str = Depends(oauth2_scheme),
    handler: GoogleOAuthHandler = Depends(get_google_oauth_handler)
) -> dict:
    """
    Dependency to verify the integrity and claims of an ID token.
    Use this for security-sensitive operations where you need to be sure the token is valid.
    """
    return await handler.verify_token(token)
