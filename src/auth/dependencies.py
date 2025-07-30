from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .handler import AuthHandler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_auth_handler():
    return AuthHandler()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    return await auth_handler.get_current_user(token)

async def verify_token(
    token: str = Depends(oauth2_scheme),
    auth_handler: AuthHandler = Depends(get_auth_handler)
):
    """
    Dependency that verifies the token is valid
    Can be used in any route that needs token verification
    """
    return await auth_handler.verify_token(token)