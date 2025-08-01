from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .handler import AzureADHandler

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authazure/token")

def get_azure_ad_handler():
    return AzureADHandler()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    handler: AzureADHandler = Depends(get_azure_ad_handler)
):
    return await handler.get_user_info(token)

async def verify_token(
    token: str = Depends(oauth2_scheme),
    handler: AzureADHandler = Depends(get_azure_ad_handler)
):
    return await handler.verify_token(token)