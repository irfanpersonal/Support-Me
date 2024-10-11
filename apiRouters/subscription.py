from fastapi import APIRouter

subscription_router = APIRouter(
    prefix = "/api/v1/subscriptions",
    tags = ["Subscription"]
)

from controllers.subscription import getAllSubscriptions, createSubscription, updateSubscription, deleteSubscription

from fastapi import Depends, Form
from utils.getDatabaseInformation import DatabaseInformation, getDatabaseInformation
from middleware.authentication import Authentication, authentication
from pydanticModels.subscription import CreateSubscriptionBody, UpdateSubscriptionBody

@subscription_router.get("/")
async def handleGetAllSubscriptions(username: str = '', page: int = 1, limit: int = 10, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation)):
    return await getAllSubscriptions(username, page, limit, databaseInformation)

@subscription_router.post("/")
async def handleCreateSubscription(createSubscriptionBody: CreateSubscriptionBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['CREATOR']))):
    return await createSubscription(createSubscriptionBody, databaseInformation, authentication)

@subscription_router.patch("/{subscription_id}")
async def handleUpdateSubscription(subscription_id: str, updateSubscriptionBody: UpdateSubscriptionBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['CREATOR']))):
    return await updateSubscription(subscription_id, updateSubscriptionBody, databaseInformation, authentication)

@subscription_router.delete("/{subscription_id}")
async def handleDeleteSubscription(subscription_id: str, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['CREATOR']))):
    return await deleteSubscription(subscription_id, databaseInformation, authentication)