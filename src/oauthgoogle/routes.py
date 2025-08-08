from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from .handler import GoogleOAuthHandler
from .schemas import UserInfo, AuthURL
from .dependencies import get_current_user, verify_token

class GoogleOAuthRoutes:
    def __init__(self):
        self.router = APIRouter(tags=["Google OAuth2 Authentication"])
        self.handler = GoogleOAuthHandler()
        self.setup_routes()

    def setup_routes(self):
        @self.router.get("/login", response_model=AuthURL)
        async def login():
            """
            Returns the Google authentication URL for the frontend to redirect to.
            """
            auth_url = self.handler.get_auth_url()
            return {"auth_url": auth_url}

        @self.router.get("/callback")
        async def callback(code: str, state: str = None):
            """
            Handles the callback from Google after user authentication.
            Exchanges the code for a token and redirects to the frontend.
            """
            token = await self.handler.get_token(code)

            # Redirect to the frontend, passing tokens as query parameters
            # The frontend should handle these tokens (e.g., store them securely)
            frontend_redirect_url = (
                f"{self.handler.config.FRONTEND_URL}/auth-google/callback"
                f"?access_token={token.access_token}"
                f"&id_token={token.id_token or ''}"
                f"&state={state or ''}"
            )
            return RedirectResponse(url=frontend_redirect_url)

        @self.router.get("/me", response_model=UserInfo)
        async def read_users_me(current_user: UserInfo = Depends(get_current_user)):
            """
            Protected endpoint to get the current authenticated user's information.
            """
            return current_user

        @self.router.get("/verify-token")
        async def verify_token_endpoint(token_data: dict = Depends(verify_token)):
            """
            Protected endpoint to verify an ID token.
            Frontend can use this to check token validity.
            """
            return {"status": "valid", "data": token_data}

        @self.router.post("/logout")
        async def logout(request: Request):
            """
            Logs the user out by revoking the token.
            The frontend should provide the token to be revoked.
            """
            # Extract token from "Authorization: Bearer <token>" header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                await self.handler.revoke_token(token)
                return JSONResponse(content={"status": "token_revoked"}, status_code=200)
            return JSONResponse(content={"error": "No token provided"}, status_code=400)
