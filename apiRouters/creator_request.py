from fastapi import APIRouter

creator_request_router = APIRouter(
    prefix = "/api/v1/creator-request",
    tags = ["Creator Request"]
)

from controllers.creator_request import getAllCreatorRequests, createCreatorRequest, updateCreatorRequest, deleteCreatorRequest
from middleware.authentication import Authentication, authentication

from fastapi import Depends, Form
from utils.getDatabaseInformation import DatabaseInformation, getDatabaseInformation
from pydanticModels.creator_request import CreateCreatorRequestBody, UpdateCreatorRequestBody

@creator_request_router.get("/")
async def handleGetAllCreatorRequests(username: str = '', status: str = '', page: int = 1, limit: int = 10, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['ADMIN']))):
    return await getAllCreatorRequests(username, status, page, limit, databaseInformation, authentication)

# To check if the user is authenticated we will use the "authentication" middleware function. 
# And it will automatically throw an error and prevent the user from accessing this route if
# they are not authenticated. 
@creator_request_router.post("/")
async def handleCreateCreatorRequest(createCreatorRequestBody: CreateCreatorRequestBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['USER']))):
    return await createCreatorRequest(createCreatorRequestBody, databaseInformation, authentication)

@creator_request_router.patch("/{creator_request_id}")
async def handleUpdateCreatorRequest(updateCreatorRequestBody: UpdateCreatorRequestBody = Form(), creator_request_id: str = '', databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['ADMIN']))):
    return await updateCreatorRequest(updateCreatorRequestBody, creator_request_id, databaseInformation, authentication)

@creator_request_router.delete("/{creator_request_id}")
async def handleDeleteCreatorRequest(creator_request_id: str, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['USER']))):
    return await deleteCreatorRequest(creator_request_id, databaseInformation, authentication)