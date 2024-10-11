from fastapi import APIRouter, Request, Header

purchase_router = APIRouter(
    prefix = "/api/v1/purchases",
    tags = ["Purchase"]
)

from controllers.purchase import createStripeCheckoutSessionForSubscription, manageSubscriptions, stripeWebhooks

from fastapi import Depends
from utils.getDatabaseInformation import DatabaseInformation, getDatabaseInformation
from middleware.authentication import Authentication, authentication
    
@purchase_router.post("/{subscription_id}/create-checkout-session")
async def handleCreateStripeCheckoutSessionForSubscription(subscription_id: str, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['USER', 'CREATOR']))):
    return await createStripeCheckoutSessionForSubscription(subscription_id, databaseInformation, authentication)

@purchase_router.patch("/manage")
async def handleManageSubscription(databaseInformation: DatabaseInformation = Depends(getDatabaseInformation), authentication: Authentication = Depends(authentication(['USER', 'CREATOR']))):
    return await manageSubscriptions(databaseInformation, authentication)

# The webhook is authenticated using the header provided on it along with the "STRIPE_WEBHOOK_KEY" so that explains the lack of the "authentication" 
# middleware logic
@purchase_router.post("/webhooks")
async def handleStripeWebhooks(request: Request, databaseInformation: DatabaseInformation = Depends(getDatabaseInformation)):
    return await stripeWebhooks(request, databaseInformation)