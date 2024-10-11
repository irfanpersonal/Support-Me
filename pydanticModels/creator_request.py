from typing import Annotated
from pydantic import BaseModel, StringConstraints
from enum import Enum

class CreateCreatorRequestBody(BaseModel):
    explanation: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 1000
    )]
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}

class CreatorRequestStatus(Enum):
    # I removed "PENDING" = "pending" because we only want to be able to switch from Pending to Rejected
    # or from Pending to Accepted.
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"

class UpdateCreatorRequestBody(BaseModel):
    status: CreatorRequestStatus
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}