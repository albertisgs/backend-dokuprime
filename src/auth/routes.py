from fastapi import APIRouter, Depends, HTTPException, status
from .handler import AuthHandler
from .schemas import UserCreate, UserLogin, Token
from .dependencies import get_auth_handler, get_current_user, verify_token

class AuthRoutes:
    def __init__(self):
        self.router = APIRouter(tags=["Authentication"])
        self.handler = AuthHandler()
        self.setup_routes()
    
    def setup_routes(self):
        @self.router.post("/register", response_model=dict, status_code=201)
        async def register(user_data: UserCreate):
            return await self.handler.create_user(user_data)
        
        @self.router.post("/sign-in", response_model=Token)
        async def login_for_access_token(user_data: UserLogin):
            return await self.handler.login(user_data)
        
        @self.router.get("/me", response_model=dict)
        async def read_users_me(current_user: dict = Depends(get_current_user)):
            return {
                "id": current_user["id"],
                "username": current_user["username"],
                "email": current_user["email"],
                "id_role": current_user.get("id_role"),
                "account_type": current_user.get("account_type")
            }
        
        @self.router.get("/verify-token")
        async def verify_token_endpoint(
            token_data: dict = Depends(verify_token)
        ):
            return {"status": "valid", "data": token_data}