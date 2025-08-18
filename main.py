from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.request.routes import RequestRoutes
from src.knowledge.routes import KnowledgeRoutes
from src.cookiesauth.routes import AuthCookiesRoutes
from src.sessionoauthgoogle.routes import GoogleOAuthCookiesRoutes
from src.sessionauthmicrosoft.routes import AzureADRCookiesoutes
from src.usermanagement.routes import router as usermanagement_router, public_router as usermanagement_public_router, authenticated_router as usermanagement_auth_router 
from src.rolemanagement.routes import router as role_management_router 
from src.uploadlegal.routes import router as legal_document_router

from fastapi.staticfiles import StaticFiles
import os

class SynchronoSyncAPI:
    def __init__(self):
        self.app = FastAPI()

        self.app.mount(
            "/public",  # URL prefix
            StaticFiles(directory=os.path.join(os.getcwd(), "public")),
            name="public"
        )


        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173", "http://172.16.8.152:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.include_routers()

    def include_routers(self):
        #request
        request_routes = RequestRoutes()
        self.app.include_router(request_routes.router, prefix="/api/request")
        #knowledgebase
        knowledge_routes = KnowledgeRoutes()
        self.app.include_router(knowledge_routes.router, prefix="/api/knowledge")
        #url upload
        self.app.include_router(legal_document_router, prefix="/api/legal-documents",)
        #auth
        auth_cookies_routes = AuthCookiesRoutes()
        self.app.include_router(auth_cookies_routes.router, prefix="/api/auth")
        azure_ad_routes = AzureADRCookiesoutes()
        self.app.include_router(azure_ad_routes.router, prefix="/api/authazure")
        google_cookies_routes = GoogleOAuthCookiesRoutes()
        self.app.include_router(google_cookies_routes.router, prefix="/api/authgoogle")
        #url user management
        self.app.include_router(usermanagement_router, prefix="/api/user-management")
        self.app.include_router(usermanagement_public_router, prefix="/api/user-management")
        self.app.include_router(usermanagement_auth_router, prefix="/api/user-management")
        self.app.include_router(role_management_router, prefix="/api/roles-management")
       


    def run(self):
        uvicorn.run(
            self.app,
            port=9898,
        )

synchrono_sync_api = SynchronoSyncAPI()
app = synchrono_sync_api.app

if __name__ == "__main__":
    synchrono_sync_api.run()