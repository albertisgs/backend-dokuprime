from fastapi import APIRouter, Depends, Response, Request
from .handler import AuthHandler
from .schemas import UserCreate, UserLogin, UserOut, StatusResponse
from ..utils.sessiondependencies import get_current_user_profile # Assuming this is your new dependency
import os

class AuthCookiesRoutes:
    def __init__(self):
        self.router = APIRouter(tags=["Authentication"])
        self.handler = AuthHandler()
        self.setup_routes()
    
    def setup_routes(self):
        @self.router.post("/register", response_model=UserOut, status_code=201)
        async def register(user_data: UserCreate):
            """Registers a new user."""
            return await self.handler.create_user(user_data)
        
        @self.router.post("/sign-in", response_model=StatusResponse)
        async def login_for_session(user_data: UserLogin, response: Response):
            """
            Authenticates a user and sets a secure, HttpOnly session cookie.
            """
            session_id = await self.handler.login_and_create_session(user_data)
            is_production = os.getenv("ENVIRONMENT") == "production"
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,        # Prevents client-side script access
                secure=is_production, # Only send over HTTPS (in production)
                samesite='lax',       # CSRF protection
                max_age=60*60*24*7    # 7 days
            )
            return {"status": "success", "message": "Logged in successfully"}

        @self.router.post("/logout", response_model=StatusResponse)
        async def logout(request: Request, response: Response):
            """
            Logs out the user by deleting the session and clearing the cookie.
            """
            session_id = request.cookies.get("session_id")
            if session_id:
                await self.handler.logout_and_delete_session(session_id)
            
            response.delete_cookie("session_id")
            return {"status": "success", "message": "Logged out successfully"}

        @self.router.get("/me", response_model=UserOut)
        async def read_users_me(current_user: dict = Depends(get_current_user_profile)):
            """
            Returns the profile of the currently logged-in user.
            Requires a valid session cookie.
            """
            print(current_user)
            return current_user

        @self.router.get("/verify-me", response_model=StatusResponse)
        async def verify_me(current_user: dict = Depends(get_current_user_profile)):
            """
            A lightweight endpoint to verify if the user's session is active.
            If this returns 200 OK, the user is considered logged in.
            """
            return {"status": "authenticated", "message": f"Welcome {current_user['username']}"}
