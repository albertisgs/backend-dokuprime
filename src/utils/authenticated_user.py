from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# Import all necessary handlers and schemas
from ..auth.handler import AuthHandler
from ..authazure.handler import AzureADHandler
from ..oauthgoogle.handler import GoogleOAuthHandler
from ..usermanagement.handler import UserManagementHandler
from ..oauthgoogle.schemas import UserInfo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_authenticated_user(token: str = Depends(oauth2_scheme)):
    """
    A universal dependency that:
    1. Verifies the token from any provider.
    2. Returns the user object without checking for a specific role.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        claims = jwt.get_unverified_claims(token)
        issuer = claims.get("iss")
        user = None
        um_handler = UserManagementHandler()

        # Logic to determine the provider and get user info
        if issuer and "https://login.microsoftonline.com" in issuer:
            handler = AzureADHandler()
            id_token_claims = await handler.verify_token(token)
            user_info = UserInfo(
                id=id_token_claims.get("oid", id_token_claims.get("sub")),
                name=id_token_claims.get("name"),
                email=id_token_claims.get("email")
            )
            if user_info.email:
                local_data = um_handler.check_email(user_info.email)
                if local_data:
                    user_info.id_role = str(local_data.get("id_role"))
            user = user_info

        elif issuer and "https://accounts.google.com" in issuer:
            handler = GoogleOAuthHandler()
            id_token_claims = await handler.verify_token(token)
            user_info = UserInfo(
                id=id_token_claims.get("sub"),
                name=id_token_claims.get("name"),
                email=id_token_claims.get("email"),
                picture=id_token_claims.get("picture")
            )
            if user_info.email:
                local_data = um_handler.check_email(user_info.email)
                if local_data:
                    user_info.id_role = str(local_data.get("id_role"))
            user = user_info

        else: # Credential-based user
            handler = AuthHandler()
            user = await handler.get_current_user(token)
        
        if not user:
            raise credentials_exception
        
        # Return the user object without any role check
        return user

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )