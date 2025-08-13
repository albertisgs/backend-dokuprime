import httpx
from fastapi import HTTPException, status
import secrets

from .config import config
from .schemas import Token, UserInfo
from .repository import MicrosoftAuthRepository

class AzureADHandler:
    def __init__(self):
        self.config = config
        self.repo = MicrosoftAuthRepository()

    def get_auth_url(self, state: str = None) -> str:
        # This method remains the same
        state = state or secrets.token_urlsafe(32)
        params = {
            "client_id": self.config.CLIENT_ID, "response_type": "code",
            "redirect_uri": self.config.REDIRECT_URI, "response_mode": "query",
            "scope": " ".join(self.config.SCOPE), "state": state
        }
        return f"{self.config.AUTHORIZATION_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    async def exchange_code_for_token(self, code: str) -> Token:
        """Exchanges the authorization code for a token from Azure AD."""
        data = {
            "client_id": self.config.CLIENT_ID, "client_secret": self.config.CLIENT_SECRET,
            "code": code, "grant_type": "authorization_code",
            "redirect_uri": self.config.REDIRECT_URI, "scope": " ".join(self.config.SCOPE)
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.config.TOKEN_URL, data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to authenticate with Azure AD: {response.text}"
                )
            return Token(**response.json())

    async def get_azure_user_info(self, access_token: str) -> UserInfo:
        """Fetches user information from Microsoft Graph API."""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get("https://graph.microsoft.com/v1.0/me", headers=headers)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to fetch user info from Microsoft Graph"
                )
            user_data = response.json()
            return UserInfo(
                id=user_data.get("id"), name=user_data.get("displayName"),
                email=user_data.get("mail") or user_data.get("userPrincipalName")
            )

    async def process_azure_login(self, code: str) -> str:
        """
        Full login flow using the "find or create" user logic.
        Returns the session ID.
        """
        token_data = await self.exchange_code_for_token(code)
        user_info = await self.get_azure_user_info(token_data.access_token)

        if not user_info.email:
            raise HTTPException(status_code=400, detail="Email not provided by Microsoft.")

        # NEW LOGIC: Find an existing user or create a new one.
        user = await self.repo.find_or_create_user(user_info)
        
        if not user:
            raise HTTPException(status_code=500, detail="Failed to process user account.")

        # Create a session for the user
        session_id = await self.repo.create_session(user_id=user["id"])
        if not session_id:
            raise HTTPException(status_code=500, detail="Could not create session.")
        return session_id