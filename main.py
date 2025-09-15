# main.py (Updated)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.request.routes import RequestRoutes
from src.knowledge.routes import KnowledgeRoutes
from src.cookiesauth.routes import AuthCookiesRoutes
from src.sessionoauthgoogle.routes import GoogleOAuthCookiesRoutes
from src.sessionauthmicrosoft.routes import AzureADRCookiesoutes
from src.notifications.routes import router as notification_router, admin_router as notification_admin_router
# --- PERUBAHAN ---
# Mengimpor semua router yang diperlukan
from src.usermanagement.routes import (
    router as usermanagement_router, 
    superadmin_router as usermanagement_superadmin_router,
    public_router as usermanagement_public_router, 
    authenticated_router as usermanagement_auth_router
)
from src.teammanagement.routes import router as team_management_router 
from src.uploadlegal.routes import( router as legal_document_router, sistem_router as legal_sistem_router)
# --- PERUBAHAN ---
# Mengimpor router untuk role management
from src.rolemanagament.routes import (
    router as role_management_router,
    superadmin_router as role_management_superadmin_router
)
#livechat
from src.live_chat.routes import (
    user_router as live_chat_user_router,
    agent_router as live_chat_agent_router
)
from src.dify_test.routes import DifyTestRoutes

from fastapi.staticfiles import StaticFiles
import os

class SynchronoSyncAPI:
    def __init__(self):
        self.app = FastAPI()
        self.app.mount(
            "/public",
            StaticFiles(directory=os.path.join(os.getcwd(), "public")),
            name="public"
        )
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5178"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.include_routers()

    def include_routers(self):
        # request
        request_routes = RequestRoutes()
        self.app.include_router(request_routes.router, prefix="/api/request")
        # knowledgebase
        knowledge_routes = KnowledgeRoutes()
        self.app.include_router(knowledge_routes.router, prefix="/api/knowledge")
        # url upload
        self.app.include_router(legal_document_router, prefix="/api/legal-documents",)
        self.app.include_router(legal_sistem_router, prefix="/api/sistem-documents",)
        # auth
        auth_cookies_routes = AuthCookiesRoutes()
        self.app.include_router(auth_cookies_routes.router, prefix="/api/auth")
        azure_ad_routes = AzureADRCookiesoutes()
        self.app.include_router(azure_ad_routes.router, prefix="/api/authazure")
        google_cookies_routes = GoogleOAuthCookiesRoutes()
        self.app.include_router(google_cookies_routes.router, prefix="/api/authgoogle")
        
        # --- PERUBAHAN ---
        # Mendaftarkan semua router user management
        self.app.include_router(usermanagement_router, prefix="/api/user-management")
        self.app.include_router(usermanagement_superadmin_router, prefix="/api/user-management")
        self.app.include_router(usermanagement_public_router, prefix="/api/user-management")
        self.app.include_router(usermanagement_auth_router, prefix="/api/user-management")
        
        # Team management tetap hanya untuk superadmin
        self.app.include_router(team_management_router, prefix="/api/teams-management")
        
        # --- PERUBAHAN ---
        # Mendaftarkan semua router role management
        self.app.include_router(role_management_router, prefix="/api/roles-management")
        self.app.include_router(role_management_superadmin_router, prefix="/api/roles-management")

        #notifikasi
        self.app.include_router(notification_router, prefix="/api/notifications")
        self.app.include_router(notification_admin_router, prefix="/api/notifications/admin")
        
        # Live Chat
        self.app.include_router(live_chat_user_router, prefix="/api")
        self.app.include_router(live_chat_agent_router, prefix="/api")
        
        #cek connection
        dify_test_routes = DifyTestRoutes()
        self.app.include_router(dify_test_routes.router, prefix="/api/dify-test")
        

    def run(self):
        uvicorn.run(
            self.app,
            port=9798,
        )

synchrono_sync_api = SynchronoSyncAPI()
app = synchrono_sync_api.app

if __name__ == "__main__":
    synchrono_sync_api.run()
