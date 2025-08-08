from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from .handler import AzureADHandler
from .schemas import Token, UserInfo, AuthURL
from .dependencies import get_azure_ad_handler, get_current_user, verify_token
from .repository import MicrosoftAuthRepository

class AzureADRoutes:
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
        async def callback(code: str, state: str = None):
            token = await self.handler.get_token(code)
            user_info = await self.handler.get_user_info(token.id_token or token.access_token)

            # Init the repository (sync)
            repo = MicrosoftAuthRepository()

            # Check if user already exists
            existing = repo.get_user_by_email(user_info.email)
            if not existing:
                role_id = repo.get_role_id_by_name(self.handler.config.DEFAULT_ROLE)
                if not role_id:
                    raise HTTPException(status_code=400, detail="Role 'financial' not found")

                repo.create_user_management(
                    id_user=user_info.id,
                    role_id=role_id,
                    email=user_info.email,
                    account_type="microsoft"
                )

            # Redirect
            frontend_redirect_url = f"{self.handler.config.FRONTEND_URL}/auth-microsoft/callback?access_token={token.access_token}&id_token={token.id_token or ''}&state={state or ''}"
            return RedirectResponse(url=frontend_redirect_url)
            

        @self.router.get("/me", response_model=UserInfo)
        async def read_users_me(current_user: UserInfo = Depends(get_current_user)):
            return current_user

        @self.router.get("/verify-token")
        async def verify_token_endpoint(
            token_data: dict = Depends(verify_token)
        ):
            return {"status": "valid", "data": token_data}
        

        @self.router.get("/logout", response_model=AuthURL)
        async def logout():
            # Azure AD logout URL
            logout_url = (
                f"https://login.microsoftonline.com/{self.handler.config.TENANT_ID}/oauth2/v2.0/logout"
                f"?post_logout_redirect_uri={self.handler.config.FRONTEND_URL}/auth-microsoft/callback?logout=logout"
            )
            return {"auth_url": logout_url}