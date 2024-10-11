from fastapi import APIRouter

user_router = APIRouter(
    prefix = "/api/v1/users",
    tags = ["User"]
)

from controllers.user import getAllUsers, showCurrentUser, updateUser

from fastapi import Depends, Form
from utils.getDatabaseInformation import DatabaseInformation, getDatabaseInformation
from middleware.authentication import Authentication, authentication
from pydanticModels.user import UpdateUserBody

@user_router.get("/")
async def handleGetAllUsers(username: str = '', limit: int = 10, page: int = 1, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation)):
    return await getAllUsers(username, limit, page, databaseInformation)

@user_router.get("/showCurrentUser")
async def handleShowCurrentUser(databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['USER', 'CREATOR', 'ADMIN']))):
    return await showCurrentUser(databaseInformation, authentication)

@user_router.patch("/updateUser")
async def handleUpdateUser(updateUserBody: UpdateUserBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['USER', 'CREATOR', 'ADMIN']))):
    return await updateUser(updateUserBody, databaseInformation, authentication)