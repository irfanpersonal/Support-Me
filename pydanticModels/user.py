from typing import Annotated
from pydantic import BaseModel, StringConstraints, EmailStr
from fastapi import UploadFile, File

class UpdateUserBody(BaseModel):
    fullName: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 256
    )]
    username: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 12
    )]
    email: Annotated[EmailStr, StringConstraints(
        min_length = 1,
        max_length = 255
    )]
    bio: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 1000
    )]
    # To make an input optional we just need to set the default value to "None"
    profilePicture: Annotated[UploadFile, File()] = None
    coverPicture: Annotated[UploadFile, File()] = None
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}