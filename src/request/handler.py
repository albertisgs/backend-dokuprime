import os
from dotenv import load_dotenv
from .repository import RequestRepository

class RequestHandler:
    def __init__(self):
        self.repo = RequestRepository()
        print("Handler Initiated")

    async def addPrompt(self, new_request: dict):
        print("Entering addPrompt function")
        usecase_name_item = new_request["usecase_name"]
        priority_item = new_request["priority"]
        user_request_item = new_request["user_request"]
        team_item = new_request["team"]
        reason_item = new_request["reason"]
        prompt_item = new_request["prompt"]
        await self.repo.addPromptRepo(usecase_name_item, priority_item, user_request_item, team_item, reason_item, prompt_item)

        print("Exiting addPrompt function")
        return {"status": 200, "message": "Operation Successfull!"}

    async def getRequests(self):
        print("Entering getRequests function")

        requests = await self.repo.getRequestRepo()

        print("Exiting getRequests function")
        return {"status": 200, "message": "Operation Successfull!", "data": requests}
    
    async def getRequestsById(self, id: int):
        print("Entering getRquestsById function")

        request = await self.repo.getRequestByIdRepo(id=id)

        print("Exiting getRquestsById function")
        return {"status": 200, "message": "Operation Successfull!", "data": request}
