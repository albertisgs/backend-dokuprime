from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import RedirectResponse
from .handler import AzureADHandler
from .schemas import AuthURL
from .config import config
import os

class AzureADRCookiesoutes:
    def __init__(self):
        self.router = APIRouter(tags=["Azure AD Authentication"])
        self.handler = AzureADHandler()
        self.setup_routes()

    def setup_routes(self):
        @self.router.get("/login", response_model=AuthURL)
        async def login():
            auth_url = self.handler.get_auth_url()
            return {"auth_url": auth_url}

        @self.router.get("/callback")
        async def callback(code: str, state: str = None): # Removed 'response: Response'
            try:
                session_id = await self.handler.process_azure_login(code)
                print(f"Generated session_id: {session_id}") # Good for debugging
                
                is_production = os.getenv("ENVIRONMENT") == "production"
                
                # --- THIS IS THE FIX ---
                # 1. Create the RedirectResponse object first.
                frontend_redirect_url = f"{self.handler.config.FRONTEND_URL}/auth-microsoft/callback?status=login-success"
                redirect_response = RedirectResponse(url=frontend_redirect_url)
                
                # 2. Set the cookie directly on that object.
                redirect_response.set_cookie(
                    key="session_id",
                    value=session_id,
                    httponly=True,
                    secure=is_production,
                    samesite='lax',
                    max_age=60*60*24*7
                )
                
                # 3. Return the modified RedirectResponse object.
                return redirect_response
            
            except Exception as e:
                print(f"Unexpected error during Azure callback: {e}")
                frontend_redirect_url = f"{self.handler.config.FRONTEND_URL}/auth-microsoft/callback?status=login-failed"
                return RedirectResponse(url=frontend_redirect_url)

        
        @self.router.get("/logout", response_model=AuthURL)
        async def logout():
            # Azure AD logout URL
            logout_url = (
                f"https://login.microsoftonline.com/{self.handler.config.TENANT_ID}/oauth2/v2.0/logout"
                f"?post_logout_redirect_uri={self.handler.config.FRONTEND_URL}/auth-microsoft/callback?logout=logout"
            )
            return {"auth_url": logout_url}