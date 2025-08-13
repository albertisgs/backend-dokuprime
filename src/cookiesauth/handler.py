from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from .repository import AuthRepository
from .schemas import UserCreate, UserLogin
import secrets

class AuthHandler:
    """
    Handles the business logic for credential-based authentication.
    It now manages session creation instead of JWT generation.
    """
    def __init__(self):
        self.repo = AuthRepository()

    async def authenticate_user(self, email: str, password: str) -> dict:
        """
        Verifies user credentials.
        Returns the full user dictionary if successful, otherwise raises an exception.
        """
        user = await self.repo.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if not self.repo.verify_password(password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        return user

    async def login_and_create_session(self, user_data: UserLogin) -> str:
        """
        Authenticates a user and creates a new session for them.
        Returns the session ID.
        """
        user = await self.authenticate_user(user_data.email, user_data.password)
        
        # Create a session in the database
        session_id = await self.repo.create_session(user_id=user["id"])
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create user session."
            )
        return session_id

    async def create_user(self, user_data: UserCreate) -> dict:
        """
        Creates a new user and their associated entry in user_management.
        """
        existing_user = await self.repo.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user_dict = user_data.dict()
        new_user = await self.repo.create_user(user_dict)
        return new_user
    
    async def logout_and_delete_session(self, session_id: str):
        """
        Deletes a user's session from the database.
        """
        await self.repo.delete_session(session_id)