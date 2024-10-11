from typing import Annotated
from pydantic import BaseModel, Field
from utils.enums import CashoutStatus

class CreateCashoutBody(BaseModel):
    # Using "Field" we can make sure that the price is an integer greater than 0
    amount: Annotated[int, Field(
        gt = 0
    )]
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}

class UpdateCashoutBody(BaseModel):
    status: CashoutStatus
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}