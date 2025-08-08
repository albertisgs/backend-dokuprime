from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# Import all three of your handlers
from ..auth.handler import AuthHandler
from ..authazure.handler import AzureADHandler
from ..oauthgoogle.handler import GoogleOAuthHandler
from ..usermanagement.handler import UserManagementHandler # Import the handler you suggested
from ..oauthgoogle.schemas import UserInfo # A universal schema for user info

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SUPERADMIN_ROLE_ID = "8ea384d2-9d47-49d7-be95-b45d08a07aa3"

async def get_current_superadmin(token: str = Depends(oauth2_scheme)):
    """
    Final universal dependency that uses the UserManagementHandler for local role lookup.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    permission_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied: Requires superadmin role.",
    )

    try:
        claims = jwt.get_unverified_claims(token)
        issuer = claims.get("iss")
        user = None

        # Instantiate the UserManagementHandler once
        um_handler = UserManagementHandler()

        if issuer and "https://login.microsoftonline.com" in issuer:
            handler = AzureADHandler()
            id_token_claims = await handler.verify_token(token)
            user_info = UserInfo(
                id=id_token_claims.get("oid", id_token_claims.get("sub")),
                name=id_token_claims.get("name"),
                email=id_token_claims.get("email")
            )
            # Use UserManagementHandler to get local role data
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
            # Use UserManagementHandler to get local role data
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

        # Role checking logic remains the same
        user_role_id = ""
        if isinstance(user, dict):
            user_role_id = user.get("id_role")
        else:
            user_role_id = getattr(user, "id_role", None)

        if str(user_role_id) != SUPERADMIN_ROLE_ID:
            raise permission_exception
        
        return user

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )