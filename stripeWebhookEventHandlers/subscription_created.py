from utils.getDatabaseInformation import DatabaseInformation
from utils.stripe import getStripe
from stripe import Event
from sqlalchemy import select

# In depth explanation of how we got access to the "user_id" and "subscription_id" from the event object
# Get access to the "user_id" located on the meta data of the "customer" object.
# customer_id = event.data.object.customer
# customer = await stripe.Customer.retrieve_async(customer_id)
# user_id = customer.metadata.user_id
# Get access to the "subscription_id" located on the meta data of the "product object"
# product_id = event["data"]["object"]["items"]["data"][0]["price"]["product"]
# product = await stripe.Product.retrieve_async(product_id)
# subscription_id = product.metadata.subscription_id

async def subscriptionCreated(event: Event, databaseInformation: DatabaseInformation) -> None:
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
        # Create the Purchase
        purchase = Models.Purchase(
            stripe_subscription_id = stripeSubscriptionId,
            user_id = user_id,
            subscription_id = subscription_id,
            status = "ACTIVE"
        )
        session.add(purchase)
        await session.commit()
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