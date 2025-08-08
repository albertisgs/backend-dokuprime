import httpx
from fastapi import HTTPException, status
from .config import config
from .schemas import Token, UserInfo
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import secrets
from .repository import MicrosoftAuthRepository

class AzureADHandler:
    def __init__(self):
        self.config = config

    def get_auth_url(self, state: str = None) -> str:
        state = state or secrets.token_urlsafe(32)
        params = {
            "client_id": self.config.CLIENT_ID,
            "response_type": "code",
            "redirect_uri": self.config.REDIRECT_URI,
            "response_mode": "query",
            "scope": " ".join(self.config.SCOPE),
            "state": state
        }
        return f"{self.config.AUTHORIZATION_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    async def get_token(self, code: str) -> Token:
        data = {
            "client_id": self.config.CLIENT_ID,
            "client_secret": self.config.CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.config.REDIRECT_URI,
            "scope": " ".join(self.config.SCOPE)
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.config.TOKEN_URL, data=data)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to authenticate with Azure AD"
                )

            token_data = response.json()
            return Token(**token_data)

    async def get_user_info(self, token: str) -> UserInfo:
        try:
            claims = jwt.get_unverified_claims(token)
            if "name" in claims and "email" in claims:
                user_info = UserInfo(
                    id=claims.get("oid", claims.get("sub")),
                    name=claims.get("name"),
                    email=claims.get("email")
                )
            else:
                async with httpx.AsyncClient() as client:
                    headers = {"Authorization": f"Bearer {token}"}
                    response = await client.get(
                        "https://graph.microsoft.com/v1.0/me",
                        headers=headers
                    )

                    if response.status_code != 200:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Failed to fetch user info from Microsoft Graph"
                        )

                    user_data = response.json()
                    user_info = UserInfo(
                        id=user_data.get("id"),
                        name=user_data.get("displayName"),
                        email=user_data.get("mail") or user_data.get("userPrincipalName")
                    )

            # Fetch role/account_type from database
            repo = MicrosoftAuthRepository()
            user_record = repo.get_user_by_email(user_info.email)
            if user_record:
                user_info.id_role = user_record[2]  # index depends on SELECT *
                user_info.account_type = user_record[4]

            return user_info

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def verify_token(self, token: str) -> dict:
        try:
            # Get Microsoft's public keys for token validation
            jwks_uri = f"https://login.microsoftonline.com/{self.config.TENANT_ID}/discovery/v2.0/keys"
            async with httpx.AsyncClient() as client:
                jwks_response = await client.get(jwks_uri)
                jwks = jwks_response.json()
            
            # Verify token with proper parameters
            claims = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],  # Azure AD uses RS256
                audience=self.config.CLIENT_ID,  # Must match your app's client ID
                issuer=f"https://login.microsoftonline.com/{self.config.TENANT_ID}/v2.0"
            )
            
            # Additional checks
            now = datetime.now().timestamp()
            if claims["exp"] < now:
                raise HTTPException(status_code=401, detail="Token expired")
                
            return claims
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )