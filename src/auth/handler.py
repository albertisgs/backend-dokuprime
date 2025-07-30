from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from .repository import AuthRepository
from .schemas import Token, TokenData, UserCreate, UserLogin
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthHandler:
    def __init__(self):
        self.repo = AuthRepository()
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, email: str, password: str):
        user = await self.repo.get_user(email)
        if not user:
            return False
        if not self.repo.verify_password(password, user["password"]):
            return False
        return user
    
    async def login(self, user_data: UserLogin):
        user = await self.authenticate_user(user_data.email, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user["username"], "email": user["email"]}, expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
    
    async def create_user(self, user_data: UserCreate):
        existing_user = await self.repo.get_user(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already registered"
            )
        
        user_dict = user_data.dict()
        new_user = await self.repo.create_user(user_dict)
        return new_user
    
    async def get_current_user(self, token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            email: str = payload.get("email") 
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username, email=email)
        except JWTError:
            raise credentials_exception
        
        user = await self.repo.get_user(email=token_data.email)
        if user is None:
            raise credentials_exception
        return user
    
    async def verify_token(self, token: str):
        """
        Verify if a JWT token is still valid (not expired)
        Returns the decoded token payload if valid
        """
        try:
            # Decode the token
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )
            
            # Check expiration
            expire = payload.get("exp")
            if expire is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has no expiration"
                )
                
            if datetime.utcnow() > datetime.fromtimestamp(expire):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
                
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    