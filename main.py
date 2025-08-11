from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.annualscrape.routes import router as annual_scrape_router 


class SynchronoSyncAPI:
    def __init__(self):
        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.include_routers()

    def include_routers(self):
        self.app.include_router(annual_scrape_router,prefix="/api/annualscrape",tags=["Annual Report Scraper"])
        


    def run(self):
        uvicorn.run(
            self.app,
            port=9898,
        )

synchrono_sync_api = SynchronoSyncAPI()
app = synchrono_sync_api.app

if __name__ == "__main__":
    synchrono_sync_api.run()