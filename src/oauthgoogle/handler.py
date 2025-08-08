import httpx
from fastapi import HTTPException, status
from jose import jwt, JWTError
import secrets

from .config import config
from .schemas import Token, UserInfo

from .repository import GoogleAuthRepository

class GoogleOAuthHandler:
    """
    Handles all the logic for Google OAuth2 authentication.
    """
    def __init__(self):
        self.config = config

    def get_auth_url(self, state: str = None) -> str:
        """
        Constructs the Google authorization URL to redirect the user to.
        """
        state = state or secrets.token_urlsafe(32)
        params = {
            "client_id": self.config.GOOGLE_CLIENT_ID,
            "redirect_uri": self.config.REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(self.config.SCOPE),
            "state": state,
            # Recommended parameters for better user experience
            "access_type": "offline",
            "prompt": "consent",
        }
        # URL-encode parameters and build the full URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.AUTHORIZATION_URL}?{query_string}"

    async def get_token(self, code: str) -> Token:
        """
        Exchanges the authorization code for an access token and ID token.
        """
        data = {
            "code": code,
            "client_id": self.config.GOOGLE_CLIENT_ID,
            "client_secret": self.config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": self.config.REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.config.TOKEN_URL, data=data)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to authenticate with Google: {response.text}"
                )

            token_data = response.json()
            return Token(**token_data)

    async def get_user_info(self, token: str) -> UserInfo:
        """
        Fetches user information from Google's userinfo endpoint using the access token.
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(self.config.USERINFO_URL, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to fetch user info from Google"
                )

            user_data = response.json()
            
            user_info= UserInfo(
                id=user_data.get("id"),  # CORRECTED: The userinfo v2 endpoint uses 'id', not 'sub'
                name=user_data.get("name"),
                email=user_data.get("email"),
                picture=user_data.get("picture"),
            )

            repo = GoogleAuthRepository()
            user_record = repo.get_user_by_email(user_info.email)
            if user_record:
                user_info.id_role = user_record[2]  # index depends on SELECT *
                user_info.account_type = user_record[4]

            return user_info

            

    async def verify_token(self, token: str) -> dict:
        """
        Verifies the ID token's signature and claims.
        This is a security-critical step.
        """
        try:
            # Get Google's public keys for token validation
            async with httpx.AsyncClient() as client:
                jwks_response = await client.get(self.config.JWKS_URL)
                jwks = jwks_response.json()
            
            # --- START OF CHANGE ---
            # Options to disable the at_hash check, which requires the access token
            options = {"verify_at_hash": False}

            # Decode and validate the token
            claims = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.config.GOOGLE_CLIENT_ID,
                issuer="https://accounts.google.com",
                options=options  # Add this line
            )
            # --- END OF CHANGE ---
            return claims
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
            
    async def revoke_token(self, token: str):
        """
        Revokes the given token, effectively logging the user out.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": token},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code != 200:
                # It's okay if revocation fails, the token will expire anyway.
                # You might want to log this for monitoring purposes.
                print(f"Warning: Failed to revoke token. Status: {response.status_code}")
