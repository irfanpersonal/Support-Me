from fastapi import Request
from fastapi.responses import JSONResponse
from utils.getDatabaseInformation import DatabaseInformation
from middleware.authentication import Authentication
from utils.custom_error import CustomError
from utils.status_codes import StatusCodes
from utils.stripe import getStripe
from sqlalchemy import select
import os
    
async def createStripeCheckoutSessionForSubscription(subscription_id: str, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        # Get access to the Stripe API 
        stripe = getStripe()
        # Check if a Purchase has been made for this subscription by this user, and if so create an error.
        purchaseRawQuery = await session.execute(
            select(Models.Purchase).filter(
                Models.Purchase.subscription_id == subscription_id,
                Models.Purchase.user_id == authentication.get('userId')
            )
        )
        purchase = purchaseRawQuery.scalar()
        # Check if a Purchase has been made for this specific subscription
        if purchase:
            # Get a hold of the Stripe Subscription Data
            stripeSubscriptionData = await stripe.Subscription.retrieve_async(purchase.stripe_subscription_id)
            # If the Subscription is currently "active"
            if stripeSubscriptionData.status == "active":
                raise CustomError('You cannot create a checkout session for something you are already subscribed to!', StatusCodes.BAD_REQUEST)
        subscriptionRawQuery = await session.execute(
            select(Models.Subscription).filter(
                Models.Subscription.id == subscription_id,
                # You are not allowed to purchase your own subscription
                Models.Subscription.user_id != authentication.get('userId')
            )
        )
        subscription = subscriptionRawQuery.scalar()
        if not subscription:
            raise CustomError('No Subscription Found with the ID Provided!', StatusCodes.NOT_FOUND)
        # Instead of creating a "PaymentIntent" which is for one time payments, we will create whats called a "Subscription"
        # object.
        # But before we can make a "Stripe Checkout Session" object its a good idea to have a "Customer ID".
        userRawQuery = await session.execute(
            select(Models.User).filter(
                Models.User.id == authentication.get('userId')
            )
        )
        user = userRawQuery.scalar()
        # Get a hold of the users "customer_id"
        customer_id = user.customer_id
        # Get a hold of the subscriptions "price_id" which can be found from the "product_id"
        all_prices_from_product = await stripe.Price.list_async(
            product = subscription.product_id
        )
        # There will only ever be ONE price associated with a product. Because of how we setup our Product creation.
        price_id = all_prices_from_product.data[0].id
        # Base URL for Success/Cancel Handling
        baseUrl = os.getenv('BASE_URL')
        # If a Purchase has already been made for this AND its "status" is set to "CANCELED" you need to create a "Stripe Checkout Session" that starts billing
        # the user from the "purchase.endDate".
        if purchase and purchase.status.name == "CANCELED":
            raise CustomError(f"You cannot create a new Stripe checkout session for a subscription you've already canceled! Instead now you need to ping the resubscribe route!", StatusCodes.BAD_REQUEST)
        else:
            # Create a Stripe Checkout Session so the user can enter in the the payment information
            stripeCheckoutSession = await stripe.checkout.Session.create_async(
                payment_method_types = ['card'],
                line_items = [
                    {
                        "price": price_id,
                        "quantity": 1
                    }
                ],
                mode = "subscription",
                customer = customer_id,
                # It is a requirement to provide a value for "success_url" and "cancel_url"
                success_url = f"{baseUrl}/success",
                cancel_url = f"{baseUrl}/subscriptions/{subscription_id}"
            )
            # Provide the Client with the "url" on the "Stripe Checkout Session Object" so they can go to a page hosted by "Stripe" to securely
            # enter in the payment information!
            return JSONResponse(
                content = {"checkout_link": stripeCheckoutSession.url},
                status_code = StatusCodes.CREATED
            )
        
async def manageSubscriptions(databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        # Get access to Stripe object
        stripe = getStripe()
        # Get "customer_id"
        userRawQuery = await session.execute(
            select(Models.User).filter(
                Models.User.id == authentication.get('userId')
            )
        )
        user = userRawQuery.scalar()
        customer_id = user.customer_id
        # Now we can create a link to the "Stripe Customer Portal". This is a link to a page hosted by Stripe for "Customers" to securely 
        # update their payment information. We will need the "customer_id" for this.
        customer_portal_session = await stripe.billing_portal.Session.create_async(
            customer = customer_id
        )
        # If you fail to go to the "https://dashboard.stripe.com/test/settings/billing/portal" site and click on the "Save changes" button you
        # won't be able to generate "customer_portal_sessions" so make sure you go to this link. Its just one button. And then your set.
        return JSONResponse(
            content = {"customer_portal_session_url": customer_portal_session.url},
            status_code = StatusCodes.OK
        )
    
# Stripe Web Hook Event Handlers
from stripeWebhookEventHandlers.subscription_created import subscriptionCreated
from stripeWebhookEventHandlers.subscription_updated import subscriptionUpdated
    
async def stripeWebhooks(request: Request, databaseInformation: DatabaseInformation) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        # Event Variable with Function Global Scope
        event = None
        # Get a hold of the Stripe object
        stripe = getStripe()
        # First we need to get access to the "Stripe Signature" which is found on the request headers under the key "Stripe-Signature"
        stripe_signature = request.headers.get('Stripe-Signature')
        # Second we need to get access to the request body
        body = await request.body()
        # Now create the Event  
        try:
            event = stripe.Webhook.construct_event(
                payload = body,
                sig_header = stripe_signature,
                secret = os.getenv('STRIPE_WEBHOOK_KEY')
            )
        except Exception as error:
            raise CustomError('Web Hook something went wrong', StatusCodes.BAD_REQUEST)
        # View Event Type
        # print('Event', event)
        # print('Event Type', event.type)
        # Created Subscription
        if event.type == 'customer.subscription.created':
            await subscriptionCreated(event, databaseInformation)
        # Updated Subscription
        if event.type == 'customer.subscription.updated':
            await subscriptionUpdated(event, databaseInformation)
        return JSONResponse(
            content = {"msg": "Stripe Webhooks"},
            status_code = StatusCodes.CREATED
        )