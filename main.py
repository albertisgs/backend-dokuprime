from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.request.routes import RequestRoutes
from src.knowledge.routes import KnowledgeRoutes

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
        request_routes = RequestRoutes()
        self.app.include_router(request_routes.router, prefix="/api/request")
        knowledge_routes = KnowledgeRoutes()
        self.app.include_router(knowledge_routes.router, prefix="/api/knowledge")

    def run(self):
        uvicorn.run(
            self.app,
            port=9898,
        )

synchrono_sync_api = SynchronoSyncAPI()
app = synchrono_sync_api.app

if __name__ == "__main__":
    synchrono_sync_api.run()