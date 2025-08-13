# src/oauthgoogle/routes.py (CORRECTED)

from fastapi import APIRouter, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from .handler import GoogleOAuthHandler
from .schemas import AuthURL, UserManagementOut, StatusResponse
from .config import config
from ..utils.sessiondependencies import get_current_user_profile 
from typing import Optional
import os

class GoogleOAuthCookiesRoutes:
    def __init__(self):
        self.router = APIRouter(tags=["Google OAuth2 Authentication"])
        self.handler = GoogleOAuthHandler()
        self.setup_routes()

    def setup_routes(self):
        @self.router.get("/login", response_model=AuthURL)
        async def login():
            auth_url = self.handler.get_auth_url()
            return {"auth_url": auth_url}

        @self.router.get("/callback")
        async def callback(code: Optional[str] = None, error: Optional[str] = None, state: Optional[str] = None):
            # Periksa jika pengguna menolak akses (access_denied)
            if error:
                error_url = f"{config.FRONTEND_URL}/auth-google/callback?status=login-failed"
                return RedirectResponse(url=error_url)

            # Pastikan 'code' ada jika tidak ada 'error'
            if not code:
                raise HTTPException(status_code=400, detail="Missing authorization code.")

            try:
                session_id = await self.handler.process_google_login(code)
                is_production = os.getenv("ENVIRONMENT") == "production"

                frontend_redirect_url = f"{config.FRONTEND_URL}/auth-google/callback?status=login-success"
                redirect_response = RedirectResponse(url=frontend_redirect_url)

                redirect_response.set_cookie(
                    key="session_id", 
                    value=session_id,
                    httponly=True, 
                    secure=is_production, 
                    samesite='lax', 
                    max_age=60*60*24*7
                )
                
                return redirect_response

            except HTTPException as e:
                if e.status_code == 403:
                    error_url = f"{config.FRONTEND_URL}/auth-google/callback?status=unauthorized"
                    return RedirectResponse(url=error_url)
                raise e
            except Exception as e:
                print(f"Unexpected error during Google callback: {e}")
                error_url = f"{config.FRONTEND_URL}/auth-google/callback?status=login-failed"
                return RedirectResponse(url=error_url)
