# ----------------------------------------------------------------------
# src/oauthgoogle/handler.py (MODIFIED)
# ----------------------------------------------------------------------

import httpx
from fastapi import HTTPException, status
import secrets

from .config import config
from .schemas import Token, UserInfo
from .repository import GoogleAuthRepository

class GoogleOAuthHandler:
    def __init__(self):
        self.config = config
        self.repo = GoogleAuthRepository()

    def get_auth_url(self, state: str = None) -> str:
        # This method remains the same
        state = state or secrets.token_urlsafe(32)
        params = {
            "client_id": self.config.GOOGLE_CLIENT_ID, "redirect_uri": self.config.REDIRECT_URI,
            "response_type": "code", "scope": " ".join(self.config.SCOPE),
            "state": state, "access_type": "offline", "prompt": "consent",
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config.AUTHORIZATION_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Token:
        # This method remains the same
        data = {
            "code": code, "client_id": self.config.GOOGLE_CLIENT_ID,
            "client_secret": self.config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": self.config.REDIRECT_URI, "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.config.TOKEN_URL, data=data)
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail=f"Failed to get token from Google: {response.text}")
            return Token(**response.json())

    async def get_google_user_info(self, access_token: str) -> UserInfo:
        # This method remains the same
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(self.config.USERINFO_URL, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to fetch user info from Google")
            user_data = response.json()
            return UserInfo(
                id=user_data.get("id"), name=user_data.get("name"),
                email=user_data.get("email"), picture=user_data.get("picture"),
            )
            
    async def process_google_login(self, code: str) -> str:
        """
        Alur login lengkap yang menemukan, membuat, atau memperbarui pengguna
        berdasarkan allowlist, lalu membuat sesi.
        """
        token_data = await self.exchange_code_for_token(code)
        user_info = await self.get_google_user_info(token_data.access_token)

        if not user_info.email:
            raise HTTPException(status_code=400, detail="Email not provided by Google.")

        # Menggunakan fungsi repository yang baru dengan logika yang disempurnakan
        user = await self.repo.process_user_login(user_info)
        
        if not user:
            raise HTTPException(status_code=403, detail="User is not authorized for Google login.")

        # Gunakan user['id'], yang merupakan UUID yang benar dari tabel `users`.
        session_id = await self.repo.create_session(user_id=user["id"]) 
        
        if not session_id:
            raise HTTPException(status_code=500, detail="Could not create session.")
        return session_id
