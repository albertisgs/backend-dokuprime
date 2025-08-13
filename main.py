from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.request.routes import RequestRoutes
from src.knowledge.routes import KnowledgeRoutes
from src.auth.routes import AuthRoutes
from src.authazure.routes import AzureADRoutes 
from src.annualscrape.routes import router as annual_scrape_router 
from src.oauthgoogle.routes import GoogleOAuthRoutes
from src.cookiesauth.routes import AuthCookiesRoutes
from src.sessionoauthgoogle.routes import GoogleOAuthCookiesRoutes
from src.sessionauthmicrosoft.routes import AzureADRCookiesoutes

# --- START OF CHANGE ---
# Import both routers from the usermanagement module
from src.usermanagement.routes import router as usermanagement_router, public_router as usermanagement_public_router, authenticated_router as usermanagement_auth_router 
# --- END OF CHANGE ---

class SynchronoSyncAPI:
    def __init__(self):
        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.include_routers()

    def include_routers(self):
        request_routes = RequestRoutes()
        self.app.include_router(request_routes.router, prefix="/api/request")
        knowledge_routes = KnowledgeRoutes()
        self.app.include_router(knowledge_routes.router, prefix="/api/knowledge")
        # auth_routes = AuthRoutes()
        # self.app.include_router(auth_routes.router, prefix="/api/auth")
        auth_cookies_routes = AuthCookiesRoutes()
        self.app.include_router(auth_cookies_routes.router, prefix="/api/auth")
        # azure_ad_routes = AzureADRoutes()
        # self.app.include_router(azure_ad_routes.router, prefix="/api/authazure")
        azure_ad_routes = AzureADRCookiesoutes()
        self.app.include_router(azure_ad_routes.router, prefix="/api/authazure")
        # google_ad_routes = GoogleOAuthRoutes()
        # self.app.include_router(google_ad_routes.router, prefix="/api/authgoogle")
        google_cookies_routes = GoogleOAuthCookiesRoutes()
        self.app.include_router(google_cookies_routes.router, prefix="/api/authgoogle")
        self.app.include_router(annual_scrape_router,prefix="/api/annualscrape",tags=["Annual Report Scraper"])
        
        self.app.include_router(usermanagement_router, prefix="/api/user-management")
        self.app.include_router(usermanagement_public_router, prefix="/api/user-management")
        self.app.include_router(usermanagement_auth_router, prefix="/api/user-management")

    def run(self):
        uvicorn.run(
            self.app,
            port=9898,
        )

synchrono_sync_api = SynchronoSyncAPI()
app = synchrono_sync_api.app

if __name__ == "__main__":
    synchrono_sync_api.run()