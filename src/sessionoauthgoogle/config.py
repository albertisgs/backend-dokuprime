import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class GoogleOAuthConfig(BaseSettings):
    """
    Configuration class for Google OAuth2.
    Loads settings from environment variables.
    """
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")
    
    # These are standard Google OAuth 2.0 endpoints
    AUTHORIZATION_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    JWKS_URL: str = "https://www.googleapis.com/oauth2/v1/certs"
    
    # Scopes required to get user's profile and email
    SCOPE: list = ["openid", "email", "profile"]
    
    # Backend redirect URI for Google to call back to
    BACKEND_URI: str = os.getenv("BACKEND_URI", "http://localhost:9898")
    REDIRECT_URI: str = f"{BACKEND_URI}{os.getenv('GOOGLE_REDIRECT_URI', '/api/authgoogle/callback')}"


# Create a single config instance to be imported by other modules
config = GoogleOAuthConfig()
