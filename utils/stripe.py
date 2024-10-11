import stripe
import os

def getStripe() -> stripe:
    # Set Stripe API Key
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    return stripe