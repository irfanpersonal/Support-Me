from fastapi.responses import JSONResponse
from utils.getDatabaseInformation import DatabaseInformation
from middleware.authentication import Authentication
from pydanticModels.creator_request import CreateCreatorRequestBody, UpdateCreatorRequestBody
from utils.custom_error import CustomError
from utils.status_codes import StatusCodes
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import math

async def getAllCreatorRequests(username: str, status: str, page: int, limit: int, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        filters = []
        skip = (page - 1) * limit
        if username:
            # If you try to query on the related data fields like so
            # filters.append(Models.CreatorRequest.user.username.ilike(f"%{username}%")) -> Error 
            # AttributeError: Neither 'InstrumentedAttribute' object nor 'Comparator' object associated with CreatorRequest.user has an attribute 'username'
            # And that's because SQLAlchemy doesn't allow filtering on fields of a related model this way. In 
            # SQLAlchemy, when filtering on fields from related models, you need to access them through the 
            # relationship using the has() or any() methods for conditions. Since user is a one-to-one 
            # relationship, you can use the has() method to filter based on the fields from the related User 
            # model.
            filters.append(Models.CreatorRequest.user.has(Models.User.username.ilike(f"%{username}%")))
        if status:
            filters.append(Models.CreatorRequest.status == status)
        # Notice how instead of just being able to access the relationship data (One to One from "user") we
        # now have to use the "options" method on the "select" method to get access to that information. The
        # reason why we have to do this now is because of the Asyncronous setup we have. During the syncronous
        # approach what would happen is something called "lazy loading". Which just means whenever you access
        # information from a relationship, behind the scenes SQLAlchemy would issue an additional query.
        # But the problem with that in an Asyncronous setup is that it won't work. Because it would need to be
        # awaited and and lazy loading does not support that. So by using the "options" approach we do all the 
        # fetching at once.
        creatorRequestsRawQuery = await session.execute(
            select(Models.CreatorRequest).filter(*filters).options(joinedload(Models.CreatorRequest.user)).offset(skip).limit(limit)
        )
        creatorRequests = creatorRequestsRawQuery.scalars().all()
        totalCreatorRequestsRawQuery = await session.execute(
            select(Models.CreatorRequest).filter(*filters)
        )
        totalCreatorRequests = len(totalCreatorRequestsRawQuery.scalars().all())
        numberOfPages = math.ceil(totalCreatorRequests / limit)
        return JSONResponse(
            content = {
                "creatorRequests": [
                    {
                        "id": creatorRequest.id,
                        "explanation": creatorRequest.explanation,
                        "status": creatorRequest.status.name,
                        "user_id": creatorRequest.user_id,
                        "user": {
                            "id": creatorRequest.user.id,
                            "fullName": creatorRequest.user.fullName,
                            "username": creatorRequest.user.username,
                            "email": creatorRequest.user.email,
                            "bio": creatorRequest.user.bio,
                            "profilePicture": creatorRequest.user.profilePicture,
                            "coverPicture": creatorRequest.user.coverPicture,
                            "role": creatorRequest.user.role.name,
                            "createdAt": str(creatorRequest.user.createdAt),
                            "updatedAt": str(creatorRequest.user.updatedAt)
                        },
                        "createdAt": str(creatorRequest.createdAt),
                        "updatedAt": str(creatorRequest.updatedAt)
                    }
                    for creatorRequest in creatorRequests
                ],
                "totalCreatorRequests": totalCreatorRequests,
                "numberOfPages": numberOfPages
            },
            status_code = StatusCodes.OK
        )

async def createCreatorRequest(createCreatorRequestBody: CreateCreatorRequestBody, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        alreadyCreatedCreatorRequestRawQuery = await session.execute(
            select(Models.CreatorRequest).filter(Models.CreatorRequest.user_id == authentication.get('userId'))
        )
        alreadyCreatedCreatorRequest = alreadyCreatedCreatorRequestRawQuery.scalar()
        if alreadyCreatedCreatorRequest:
            raise CustomError('You already created a creator request!', StatusCodes.BAD_REQUEST)
        creator_request = Models.CreatorRequest(
            explanation = createCreatorRequestBody.explanation,
            user_id = authentication.get('userId')
        )
        session.add(creator_request)
        await session.commit()
        await session.refresh(creator_request)
        return JSONResponse(
            content = {
                "creatorRequest": {
                    "id": creator_request.id,
                    "explanation": creator_request.explanation,
                    "status": creator_request.status.name,
                    "user_id": creator_request.user_id,
                }
            },
            status_code = StatusCodes.CREATED
        )
    
async def updateCreatorRequest(updateCreatorRequestBody: UpdateCreatorRequestBody, creator_request_id: str, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        creatorRequestRawQuery = await session.execute(
            select(Models.CreatorRequest).filter(
                Models.CreatorRequest.id == creator_request_id
            ).options(joinedload(Models.CreatorRequest.user))
        )
        creatorRequest = creatorRequestRawQuery.scalar()
        if creatorRequest.status.name == 'REJECTED' or creatorRequest.status.name == 'ACCEPTED':
            raise CustomError('You already accepted/rejected this creator request!', StatusCodes.BAD_REQUEST)
        if not creatorRequest:
            raise CustomError('No Creator Request Found with the ID Provided!', StatusCodes.NOT_FOUND)
        # Update the Creator Status
        creatorRequest.status = updateCreatorRequestBody.status.name
        # If the status is "ACCEPTED" we must update the logged in users role to "CREATOR"
        userRawQuery = await session.execute(
            select(Models.User).filter(
                Models.User.id == creatorRequest.user_id
            )
        )
        user = userRawQuery.scalar()
        if updateCreatorRequestBody.status.name == 'ACCEPTED':
            user.role = "CREATOR"
        # The moment you invoke the "commit()" method on the "session" object you will lose all the data associated with 
        # the queried result. For example if you try to do something like "creatorRequest.explanation = "NEW VALUE"""
        # that will create an error. Think of it like this: creatorRequest = None, and this is something we can actually
        # configure. Because by default it has the keyword argument "expire_on_commit" to "True". So by setting this 
        # to "False" we can change this default behavior.
        await session.commit()
        # To prevent that error we have to use the "refresh" method on the "session" object. This will refetch the data
        # associated with it so you can use it.
        await session.refresh(creatorRequest)
        return JSONResponse(
            content = {
                "creatorRequest": {
                    "id": creatorRequest.id,
                    "explanation": creatorRequest.explanation,
                    "status": creatorRequest.status.name,
                    "user_id": creatorRequest.user_id,
                    "user": {
                        "id": creatorRequest.user.id,
                        "fullName": creatorRequest.user.fullName,
                        "username": creatorRequest.user.username,
                        "email": creatorRequest.user.email,
                        "bio": creatorRequest.user.bio,
                        "profilePicture": creatorRequest.user.profilePicture,
                        "coverPicture": creatorRequest.user.coverPicture,
                        "role": creatorRequest.user.role.name,
                        "createdAt": str(creatorRequest.user.createdAt),
                        "updatedAt": str(creatorRequest.user.updatedAt)
                    },
                    "createdAt": str(creatorRequest.createdAt),
                    "updatedAt": str(creatorRequest.updatedAt)
                }
            },
            status_code = StatusCodes.OK
        )
    
async def deleteCreatorRequest(creator_request_id: str, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        creatorRequestRawQuery = await session.execute(
            select(Models.CreatorRequest).filter(
                Models.CreatorRequest.id == creator_request_id,
                Models.CreatorRequest.user_id == authentication.get('userId')
            )
        )
        creatorRequest = creatorRequestRawQuery.scalar()
        if not creatorRequest:
            raise CustomError('No Creator Request Found with the ID Provided!', StatusCodes.NOT_FOUND)
        
        # We don't have to worry about making sure that they can't delete a "Creator Request" post acceptance as a creator because the role required will 
        # change. So they won't even be able to access this endpoint.

        # Using the "delete()" method on its own won't work. You need to use the "await" keyword otherwise it won't be staged for actual deletion
        await session.delete(creatorRequest)
        # And finally the "commit()" method, which will perform the actual deletion.
        await session.commit()
        return JSONResponse(
            content = {"msg": "Deleted Creator Request"},
            status_code = StatusCodes.CREATED
        )