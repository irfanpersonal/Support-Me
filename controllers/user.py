from fastapi.responses import JSONResponse
from utils.getDatabaseInformation import DatabaseInformation
from middleware.authentication import Authentication
from pydanticModels.user import UpdateUserBody
from utils.custom_error import CustomError
from utils.status_codes import StatusCodes
from utils.deleteFile import deleteFile
import aiofiles
from uuid import uuid4
from sqlalchemy import select, or_
from werkzeug.utils import secure_filename
import math

async def showCurrentUser(databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        userRawQuery = await session.execute(
            select(Models.User).filter(Models.User.id == authentication.get('userId'))
        )
        user = userRawQuery.scalar()
        return JSONResponse(
            content = {
                "user": {
                    "id": user.id,
                    "fullName": user.fullName,
                    "username": user.username,
                    "email": user.email,
                    "bio": user.bio,
                    "profilePicture": user.profilePicture,
                    "coverPicture": user.coverPicture,
                    "role": user.role.name,
                    "createdAt": str(user.createdAt),
                    "updatedAt": str(user.updatedAt)
                }
            },
            status_code = StatusCodes.OK
        )

async def getAllUsers(username, limit, page, databaseInformation: DatabaseInformation) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        filters = [
            Models.User.role != 'ADMIN'
        ]
        skip = (page - 1) * limit
        if username:
            filters.append(Models.User.username.ilike(f"%{username}%"))
        usersRawQuery = await session.execute(
            select(Models.User).filter(*filters).offset(skip).limit(limit)
        )
        users = usersRawQuery.scalars().all()
        totalUsersRawQuery = await session.execute(
            select(Models.User).filter(*filters)
        )
        totalUsers = len(totalUsersRawQuery.scalars().all())
        numberOfPages = math.ceil(totalUsers / limit)
        return JSONResponse(
            content = {
                "users": [
                    {
                        "id": user.id,
                        "fullName": user.fullName,
                        "username": user.username,
                        "email": user.email,
                        "bio": user.bio,
                        "profilePicture": user.profilePicture,
                        "coverPicture": user.coverPicture,
                        "role": user.role.name,
                        "createdAt": str(user.createdAt),
                        "updatedAt": str(user.updatedAt)
                    }
                    for user in users
                ],
                "totalUsers": totalUsers,
                "numberOfPages": numberOfPages
            }
        )
    
async def updateUser(updateUserBody: UpdateUserBody, databaseInformation: DatabaseInformation, authentication: Authentication):
    Session, Models = databaseInformation
    async with Session() as session:
        # Get a hold of the currently logged in user
        userRawQuery = await session.execute(
            select(Models.User).filter(
                Models.User.id == authentication.get('userId')
            )
        )
        user = userRawQuery.scalar()
        # Check if the provided username and email conflict with any preexisting users. And if so throw an error.
        conditions = []
        if user.username != updateUserBody.username:
            conditions.append(Models.User.username == updateUserBody.username)
        if user.email != updateUserBody.email:
            conditions.append(Models.User.email == updateUserBody.email)
        if conditions:
            alreadyExistRawQuery = await session.execute(
                select(Models.User).filter(
                    or_(*conditions)
                )
            )
            alreadyExists = alreadyExistRawQuery.scalar()
            if alreadyExists:
                raise CustomError('Someone is already using the provided username/email!', StatusCodes.BAD_REQUEST)
        # Check if a Profile Picture or Cover Picture is Provided
        if updateUserBody.profilePicture:
            # Check if File is of type Image, if not throw an error
            if not updateUserBody.profilePicture.content_type.startswith('image'):
                raise CustomError('Profile Picture must be an Image!', StatusCodes.BAD_REQUEST)
            # Check if Image is not exceeding the size limit
            if updateUserBody.profilePicture.size > (1024 * 1024) * 2:
                raise CustomError('The profile picture size must not exceed 2MB!', StatusCodes.BAD_REQUEST)
            # Check if an existing value exists already and if so delete it
            profilePictureLocationWithoutFirstSlash = user.profilePicture[1:]
            deleteFile(profilePictureLocationWithoutFirstSlash)
            # Upload New Image
            file_location = f"static/uploads/profile_pictures/{updateUserBody.username}_{uuid4()}_{secure_filename(updateUserBody.profilePicture.filename)}"
            async with aiofiles.open(file_location, "wb") as file:
                content = await updateUserBody.profilePicture.read()
                await file.write(content) 
            # Update Instition Image Value
            user.profilePicture = f"/{file_location}"
            await session.commit()
            await session.refresh(user)
        if updateUserBody.coverPicture:
            # Check if File is of type Image, if not throw an error
            if not updateUserBody.coverPicture.content_type.startswith('image'):
                raise CustomError('Cover Picture must be an Image!', StatusCodes.BAD_REQUEST)
            # Check if Image is not exceeding the size limit
            if updateUserBody.coverPicture.size > (1024 * 1024) * 2:
                raise CustomError('The cover picture size must not exceed 2MB!', StatusCodes.BAD_REQUEST)
            # Check if an existing value exists already and if so delete it
            coverPictureLocationWithoutFirstSlash = user.coverPicture[1:]
            deleteFile(coverPictureLocationWithoutFirstSlash)
            # Upload New Image
            file_location = f"static/uploads/cover_pictures/{updateUserBody.username}_{uuid4()}_{secure_filename(updateUserBody.coverPicture.filename)}"
            async with aiofiles.open(file_location, "wb") as file:
                content = await updateUserBody.coverPicture.read()
                await file.write(content) 
            # Update Instition Image Value
            user.coverPicture = f"/{file_location}"
            await session.commit()
            await session.refresh(user)
        return JSONResponse(
            content = {
                "user": {
                    "id": user.id,
                    "fullName": user.fullName,
                    "username": user.username,
                    "email": user.email,
                    "bio": user.bio,
                    "profilePicture": user.profilePicture,
                    "coverPicture": user.coverPicture,
                    "role": user.role.name,
                    "createdAt": str(user.createdAt),
                    "updatedAt": str(user.updatedAt)
                }
            },
            status_code = StatusCodes.OK
        )