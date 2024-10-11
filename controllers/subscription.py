from fastapi.responses import JSONResponse
from utils.getDatabaseInformation import DatabaseInformation
from middleware.authentication import Authentication
from pydanticModels.subscription import CreateSubscriptionBody, UpdateSubscriptionBody
from utils.custom_error import CustomError
from utils.status_codes import StatusCodes
from utils.stripe import getStripe
from utils.deleteFile import deleteFile
from utils.enums import PurchaseStatus
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from uuid import uuid4
import math
import aiofiles

async def getAllSubscriptions(username: str, page: int, limit: int, databaseInformation: DatabaseInformation) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        filters = []
        skip = (page - 1) * limit
        if username:
            filters.append(Models.Subscription.user.has(Models.User.username.ilike(f"%{username}%")))
        # In simple terms when you use "joinedload" inside of the "options" method its similar to using the "populate" method
        # from Mongoose. You are asking it to be filled with the associated data. 
        subscriptionsRawQuery = await session.execute(
            select(Models.Subscription).filter(*filters).options(joinedload(Models.Subscription.user)).offset(skip).limit(limit)
        )
        subscriptions = subscriptionsRawQuery.scalars().all()
        totalSubscriptionsRawQuery = await session.execute(
            select(Models.Subscription).filter(*filters)
        )
        totalSubscriptions = len(totalSubscriptionsRawQuery.scalars().all())
        numberOfPages = math.ceil(totalSubscriptions / limit)
        return JSONResponse(
            content = {
                "subscriptions": [
                    {
                        "id": subscription.id,
                        "title": subscription.title,
                        "description": subscription.description,
                        "price": subscription.price,
                        "user_id": subscription.user_id,
                        "user": {
                            "id": subscription.user.id,
                            "fullName": subscription.user.fullName,
                            "username": subscription.user.username,
                            "email": subscription.user.email,
                            "bio": subscription.user.bio,
                            "profilePicture": subscription.user.profilePicture,
                            "coverPicture": subscription.user.coverPicture,
                            "role": subscription.user.role.name,
                            "createdAt": str(subscription.user.createdAt),
                            "updatedAt": str(subscription.user.updatedAt)
                        }
                    }
                    for subscription in subscriptions
                ],
                "totalSubscriptions": totalSubscriptions,
                "numberOfPages": numberOfPages
            },
            status_code = StatusCodes.OK
        )
    
async def createSubscription(createSubscriptionBody: CreateSubscriptionBody, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        amountOfSubscriptionsRawQuery = await session.execute(
            select(Models.Subscription).filter(
                Models.Subscription.user_id == authentication.get('userId')
            )
        )
        amountOfSubscriptions = len(amountOfSubscriptionsRawQuery.scalars().all())
        if amountOfSubscriptions == 3:
            raise CustomError('A creator is limited to creating a maximum of 3 subscription types!', StatusCodes.BAD_REQUEST)
        # If a Image is not provided throw an error, image.size is equal to bytes
        if createSubscriptionBody.image.size == 0:
            raise CustomError('Please check all inputs!', StatusCodes.BAD_REQUEST)
        # Check if File is of type Image, if not throw an error
        if not createSubscriptionBody.image.content_type.startswith('image'):
            raise CustomError('File Type must be an Image!', StatusCodes.BAD_REQUEST)
        # Check if Image Size is not larger than max size of 2MB
        if createSubscriptionBody.image.size > (1024 * 1024) * 2:
            raise CustomError('The image size must not exceed 2MB!', StatusCodes.BAD_REQUEST)
        # Save the Image
        file_location = f"static/uploads/subscription_images/{authentication.get('username')}_{uuid4()}_{secure_filename(createSubscriptionBody.image.filename)}"
        # If the file at this location does not exist create one, and we wan't to set the mode to "wb" for
        # write bytes. Because we are dealing with an image not some text. And things like images, videos,
        # and pdfs require it to be done in binary.
        async with aiofiles.open(file_location, "wb") as file:
            content = await createSubscriptionBody.image.read()
            await file.write(content)
        # At this point we have to make the Stripe Product. This is so that when we create the "Subscription" object we will now
        # have both the customer_id and product_id. 
        stripe = getStripe()
        product = await stripe.Product.create_async(
            # The product we are creating here does not require you to input the price, this is simply for defining
            # what it is your selling/offering to the consumer/customer. As a best practice always provide a name and
            # description.
            name = createSubscriptionBody.title,
            description = createSubscriptionBody.description
        )
        # Now we can create a Price object because of the Product ID
        await stripe.Price.create_async(
            currency = "usd",
            unit_amount = createSubscriptionBody.price,
            # Its very important that we add this line of code here, this will make it so that its a payment that needs to be done every month, it
            # also has awesome type hints.
            recurring = {"interval": "month"},
            # You MUST provide either "product" or "product_data"
            # product - pass in the product_id
            product = product.id
        )
        subscription = Models.Subscription(
            title = createSubscriptionBody.title,
            description = createSubscriptionBody.description,
            price = createSubscriptionBody.price,
            image = f"/{file_location}",
            product_id = product.id,
            user_id = authentication.get('userId')
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        # Update the "Stripe Product" to include metadata for the "subscription_id"
        await stripe.Product.modify_async(
            product.id,
            metadata = {
                "subscription_id": subscription.id
            }
        )
        return JSONResponse(
            content = {
                "subscription": {
                    "id": subscription.id,
                    "title": subscription.title,
                    "description": subscription.description,
                    "price": subscription.price,
                    "image": subscription.image,
                    "product_id": subscription.product_id,
                    "user_id": subscription.user_id,
                }
            },
            status_code = StatusCodes.CREATED
        )
    
async def updateSubscription(subscription_id: str, updateSubscriptionBody: UpdateSubscriptionBody, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        subscriptionRawQuery = await session.execute(
            select(Models.Subscription).filter(
                Models.Subscription.id == subscription_id,
                Models.Subscription.user_id == authentication.get('userId')
            ).options(joinedload(Models.Subscription.user))
        )
        subscription = subscriptionRawQuery.scalar()
        if not subscription:
            raise CustomError('No Subscription Found with the ID Provided!', StatusCodes.NOT_FOUND)
        # To update the Stripe Product use the "product_id"
        stripe = getStripe()
        await stripe.Product.modify_async(
            # id - Stripe Product ID
            id = subscription.product_id,
            name = updateSubscriptionBody.title,
            description = updateSubscriptionBody.description
        )
        subscription.title = updateSubscriptionBody.title
        subscription.description = updateSubscriptionBody.description
        # Check if a Image is Provided
        if updateSubscriptionBody.image:
            # Check if File is of type Image, if not throw an error
            if not updateSubscriptionBody.image.content_type.startswith('image'):
                raise CustomError('File Type must be an Image!', StatusCodes.BAD_REQUEST)
            # Check if Image is not exceeding the size limit
            if updateSubscriptionBody.image.size > (1024 * 1024) * 2:
                raise CustomError('Image size must not exceed 2MB!', StatusCodes.BAD_REQUEST)
            # Check if an existing value exists already and if so delete it
            imageLocationWithoutFirstSlash = subscription.image[1:]
            deleteFile(imageLocationWithoutFirstSlash)
            # Upload New Image
            file_location = f"static/uploads/subscription_images/{authentication.get('username')}_{uuid4()}_{secure_filename(updateSubscriptionBody.image.filename)}"
            async with aiofiles.open(file_location, "wb") as file:
                content = await updateSubscriptionBody.image.read()
                await file.write(content) 
            # Update Subscription Image Value
            subscription.image = f"/{file_location}"
        await session.commit()
        await session.refresh(subscription)
        return JSONResponse(
            content = {
                "subscription": {
                    "id": subscription.id,
                    "title": subscription.title,
                    "description": subscription.description,
                    "price": subscription.price,
                    "user_id": subscription.user_id,
                    "user": {
                        "id": subscription.user.id,
                        "fullName": subscription.user.fullName,
                        "username": subscription.user.username,
                        "email": subscription.user.email,
                        "bio": subscription.user.bio,
                        "profilePicture": subscription.user.profilePicture,
                        "coverPicture": subscription.user.coverPicture,
                        "role": subscription.user.role.name,
                        "createdAt": str(subscription.user.createdAt),
                        "updatedAt": str(subscription.user.updatedAt)
                    }
                }
            },
            status_code = StatusCodes.OK
        )
    
async def deleteSubscription(subscription_id: str, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        # Get access to Stripe
        stripe = getStripe()
        # Check if this is even your subscription to delete
        subscriptionRawQuery = await session.execute(
            select(Models.Subscription).filter(
                Models.Subscription.id == subscription_id,
                Models.Subscription.user_id == authentication.get('userId')
            )
        )
        subscription = subscriptionRawQuery.scalar()
        if not subscription:
            raise CustomError('No Subscription Found with the ID Provided!', StatusCodes.NOT_FOUND)
        # Change Status of all Purchases if any for this Subscription("referred to Product in Stripe") to "EXPIRED", because 
        # internally Stripe stops payment for a product/subscription that has been deleted, so you don't need to worry about
        # users being charged post product/subscription deletion.
        purchases = (await session.execute(
            select(Models.Purchase).filter(
                Models.Purchase.subscription_id == subscription_id
            )
        )).scalars().all()
        # Iterate over each purchase and set the "status" property to "EXPIRED" and cancel the subscription on Stripe
        for purchase in purchases:
            purchase.status = "EXPIRED"
            await stripe.Subscription.cancel_async(purchase.stripe_subscription_id)
        # Save these changes
        await session.commit()
        # To keep the controller clean and avoid cluttering it with the image deletion process, we'll 
        # move that logic to the Subscription model instead.
        await session.delete(subscription)
        await session.commit()
        return JSONResponse(
            content = {"msg": "Deleted Subscription!"},
            status_code = StatusCodes.OK
        )