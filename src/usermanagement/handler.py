from .repository import UserManagementRepository
from .schemas import UserManagementCreate, UserManagementUpdate
from fastapi import HTTPException

class UserManagementHandler:
    def __init__(self):
        self.repo = UserManagementRepository()

    def list_users(self):
        return self.repo.list_all()

    def get_user(self, id: str):
        return self.repo.get_by_id(id)

    def create_user(self, data: UserManagementCreate):
        return self.repo.create(data)

    def update_user(self, id: str, data: UserManagementUpdate):
        return self.repo.update(id, data)

    def delete_user(self, id: str):
        return self.repo.delete(id)
    
    def check_email(self, email:str):
        return self.repo.check(email)

    def list_roles(self):
        return self.repo.list_roles()
    
    def get_role(self, role_id: str):
        role = self.repo.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role