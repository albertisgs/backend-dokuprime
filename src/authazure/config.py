import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class AzureADConfig(BaseSettings):
    CLIENT_ID: str = os.getenv("AZURE_AD_CLIENT_ID")
    FRONTEND_URL: str = os.getenv("FRONTEND_AZURE_AUTH_CALLBACK_URI")
    CLIENT_SECRET: str = os.getenv("AZURE_AD_CLIENT_SECRET")
    TENANT_ID: str = os.getenv("AZURE_AD_TENANT_ID")
    AUTHORITY: str = f"https://login.microsoftonline.com/{os.getenv('AZURE_AD_TENANT_ID')}"
    SCOPE: list = ["openid", "profile", "email", "User.Read"]
    BACKEND_URI: str = os.getenv("BACKEND_URI", "http://localhost:9898")
    REDIRECT_URI: str = f"{BACKEND_URI}{os.getenv('AZURE_AD_REDIRECT_URI', '/api/authazure/callback')}"
    TOKEN_URL: str = f"https://login.microsoftonline.com/{os.getenv('AZURE_AD_TENANT_ID')}/oauth2/v2.0/token"
    AUTHORIZATION_URL: str = f"https://login.microsoftonline.com/{os.getenv('AZURE_AD_TENANT_ID')}/oauth2/v2.0/authorize"


config = AzureADConfig()