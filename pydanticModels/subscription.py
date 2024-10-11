from typing import Annotated
from pydantic import BaseModel, StringConstraints, Field
from fastapi import UploadFile, File

class CreateSubscriptionBody(BaseModel):
    title: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 256
    )]
    description: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 1000
    )]
    # Using "Field" we can make sure that the price is an integer greater than 0
    price: Annotated[int, Field(
        gt = 0
    )]
    # An Image for the Subscription
    image: Annotated[UploadFile, File()]
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}

class UpdateSubscriptionBody(BaseModel):
    title: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 256
    )]
    description: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 1000
    )]
    # Not going to allow price change! You must delete subscription to change price!
    # Made updating the image for Subscription optional.
    image: Annotated[UploadFile, File()] = None
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}