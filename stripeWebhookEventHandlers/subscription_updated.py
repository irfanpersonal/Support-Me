from utils.getDatabaseInformation import DatabaseInformation
from utils.stripe import getStripe
from stripe import Event
from sqlalchemy import select
import time

# In depth explanation of how we got access to the "user_id" and "subscription_id" from the event object
# Get access to the "user_id" located on the meta data of the "customer" object.
# customer_id = event.data.object.customer
# customer = await stripe.Customer.retrieve_async(customer_id)
# user_id = customer.metadata.user_id
# Get access to the "subscription_id" located on the meta data of the "product object"
# product_id = event["data"]["object"]["items"]["data"][0]["price"]["product"]
# product = await stripe.Product.retrieve_async(product_id)
# subscription_id = product.metadata.subscription_id

async def subscriptionUpdated(event: Event, databaseInformation: DatabaseInformation) -> None:
    Session, Models = databaseInformation
    async with Session() as session:
        # Get access to the "Stripe" object
        stripe = getStripe()
        # Get "user_id"
        user_id = (await stripe.Customer.retrieve_async(event.data.object.customer)).metadata.user_id
        # Get "subscription_id"
        subscription_id = (await stripe.Product.retrieve_async(event["data"]["object"]["items"]["data"][0]["price"]["product"])).metadata.subscription_id
        # Get "Stripe Subscription ID"
        stripeSubscriptionId = event.data.object.id     
        # Now we need to handle three cases
        # Case 0 - a user has already made the purchase and is being charged again (so 1 month has passed)
        # Case 1 - a user has successfully payed the subscription (this is an extra event that occurs post "customer.subscription.created")
        # Case 2 - a user has "Cancel plan"
        # Case 3 - a user has "Renew plan"
        # Case 0 - Check if a Purchase has already been made and if so increase the amount of the user who created the subscription for people to purchase
        previous_attributes = event.data.previous_attributes
        alreadyMadePurchase = (await session.execute(
            select(Models.Purchase).filter(
                Models.Purchase.subscription_id == subscription_id,
                Models.Purchase.user_id == user_id
            )
        )).scalar()
        # For recurring payments only logic (so like a month ahead they will collect payment again)
        if alreadyMadePurchase and previous_attributes.get('latest_invoice'):
            # Update Amount on User who created the "Subscription" for people to purchase
            subscriptionData = (await session.execute(
                select(Models.Subscription).filter(
                    Models.Subscription.id == subscription_id
                )
            )).scalar()
            price = subscriptionData.price
            user_who_created_subscription_for_people_to_purchase = subscriptionData.user_id
            user = (await session.execute(
                select(Models.User).filter(
                    Models.User.id == user_who_created_subscription_for_people_to_purchase
                )
            )).scalar()
            user.amount = user.amount + price
            await session.commit()
            # The amount is in the Stripe Lowest Currency Format
            return
        # Case 1
        if not previous_attributes.get('default_payment_method') and previous_attributes.get('status') == "incomplete":
            return
        # Case 2
        elif not previous_attributes.get('cancel_at') and not previous_attributes.get('cancel_at_period_end') and not previous_attributes.get('canceled_at') and not previous_attributes.get('cancellation_details').get('reason'):
            purchaseRawQuery = await session.execute(
                select(Models.Purchase).filter(
                    Models.Purchase.stripe_subscription_id == stripeSubscriptionId,
                    Models.Purchase.user_id == user_id,
                    Models.Purchase.subscription_id == subscription_id,
                )
            )
            purchase = purchaseRawQuery.scalar()
            purchase.status = "CANCELED"
            await session.commit()
        # Case 3
        elif previous_attributes.get('cancel_at') and previous_attributes.get('cancel_at_period_end') and previous_attributes.get('canceled_at') and previous_attributes.get('cancellation_details').get('reason'):
            purchaseRawQuery = await session.execute(
                select(Models.Purchase).filter(
                    Models.Purchase.stripe_subscription_id == stripeSubscriptionId,
                    Models.Purchase.user_id == user_id,
                    Models.Purchase.subscription_id == subscription_id,
                )
            )
            purchase = purchaseRawQuery.scalar()
            purchase.status = "ACTIVE"
            await session.commit()