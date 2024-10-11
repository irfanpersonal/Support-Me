from fastapi import APIRouter

cashout_router = APIRouter(
    prefix = "/api/v1/cashout",
    tags = ["Cashout"]
)

from controllers.cashout import getAllCashouts, getAllUserCashouts, createCashout, updateCashout

from fastapi import Depends, Form
from utils.getDatabaseInformation import DatabaseInformation, getDatabaseInformation
from pydanticModels.cashout import CreateCashoutBody, UpdateCashoutBody
from middleware.authentication import Authentication, authentication
    
@cashout_router.get("/")
async def handleGetAllUserCashouts(username: str = '', page: int = 1, limit: int = 10, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['ADMIN']))):
    return await getAllCashouts(username, page, limit, databaseInformation, authentication)

@cashout_router.get("/personal")
async def handleGetAllUserCashouts(page: int = 1, limit: int = 10, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['CREATOR']))):
    return await getAllUserCashouts(page, limit, databaseInformation, authentication)

@cashout_router.post("/")
async def handleCreateCashout(createCashoutBody: CreateCashoutBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['CREATOR']))):
    return await createCashout(createCashoutBody, databaseInformation, authentication)

@cashout_router.patch("/{cashout_id}")
async def handleUpdateCashout(cashout_id: str, updateCashoutBody: UpdateCashoutBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['ADMIN']))):
    return await updateCashout(cashout_id, updateCashoutBody, databaseInformation, authentication)