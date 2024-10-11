from typing import Annotated
from pydantic import BaseModel, StringConstraints, EmailStr
from fastapi import UploadFile, File

class RegisterBody(BaseModel):
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
    password: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 60
    )]
    bio: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 1000
    )]
    profilePicture: Annotated[UploadFile, File()]
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}

class LoginBody(BaseModel):
    email: Annotated[EmailStr, StringConstraints(
        min_length = 1,
        max_length = 256
    )]
    password: Annotated[str, StringConstraints(
        min_length = 1,
        max_length = 60
    )]
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}

class VerifyEmailBody(BaseModel):
    email: Annotated[EmailStr, StringConstraints(
        min_length = 1,
        max_length = 256
    )]
    verificationToken: Annotated[str, StringConstraints(
        min_length = 1
    )]
    # If a Client tries to send some extra data, they will receive an error response. So basically send
    # me exactly what I have defined and nothing more!
    model_config = {"extra": "forbid"}