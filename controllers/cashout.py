from fastapi.responses import JSONResponse
from utils.getDatabaseInformation import DatabaseInformation
from middleware.authentication import Authentication
from pydanticModels.cashout import CreateCashoutBody, UpdateCashoutBody
from utils.custom_error import CustomError
from utils.status_codes import StatusCodes
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import math

async def getAllCashouts(username: str, page: int, limit: int, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        filters = []
        skip = (page - 1) * limit
        if username:
            filters.append(Models.Cashout.user.has(Models.User.username.ilike(f"%{username}%")))
        # In simple terms when you use "joinedload" inside of the "options" method its similar to using the "populate" method
        # from Mongoose. You are asking it to be filled with the associated data. 
        cashoutsRawQuery = await session.execute(
            select(Models.Cashout).filter(*filters).options(joinedload(Models.Cashout.user)).offset(skip).limit(limit)
        )
        cashouts = cashoutsRawQuery.scalars().all()
        totalCashoutsRawQuery = await session.execute(
            select(Models.Cashout).filter(*filters)
        )
        totalCashouts = len(totalCashoutsRawQuery.scalars().all())
        numberOfPages = math.ceil(totalCashouts / limit)
        return JSONResponse(
            content = {
                "cashouts": [
                    {
                        "id": cashout.id,
                        "amount": cashout.amount,
                        "user_id": cashout.user_id,
                        "user": {
                            "id": cashout.user.id,
                            "fullName": cashout.user.fullName,
                            "username": cashout.user.username,
                            "email": cashout.user.email,
                            "bio": cashout.user.bio,
                            "profilePicture": cashout.user.profilePicture,
                            "coverPicture": cashout.user.coverPicture,
                            "role": cashout.user.role.name,
                            "createdAt": str(cashout.user.createdAt),
                            "updatedAt": str(cashout.user.updatedAt)
                        }
                    }
                    for cashout in cashouts
                ],
                "totalCashouts": totalCashouts,
                "numberOfPages": numberOfPages
            },
            status_code = StatusCodes.OK
        )
    
async def getAllUserCashouts(page: int, limit: int, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        filters = [
            Models.Cashout.user_id == authentication.get('userId')
        ]
        skip = (page - 1) * limit
        # In simple terms when you use "joinedload" inside of the "options" method its similar to using the "populate" method
        # from Mongoose. You are asking it to be filled with the associated data. 
        cashoutsRawQuery = await session.execute(
            select(Models.Cashout).filter(*filters).options(joinedload(Models.Cashout.user)).offset(skip).limit(limit)
        )
        cashouts = cashoutsRawQuery.scalars().all()
        totalCashoutsRawQuery = await session.execute(
            select(Models.Cashout).filter(*filters)
        )
        totalCashouts = len(totalCashoutsRawQuery.scalars().all())
        numberOfPages = math.ceil(totalCashouts / limit)
        return JSONResponse(
            content = {
                "cashouts": [
                    {
                        "id": cashout.id,
                        "amount": cashout.amount,
                        "user_id": cashout.user_id,
                        "user": {
                            "id": cashout.user.id,
                            "fullName": cashout.user.fullName,
                            "username": cashout.user.username,
                            "email": cashout.user.email,
                            "bio": cashout.user.bio,
                            "profilePicture": cashout.user.profilePicture,
                            "coverPicture": cashout.user.coverPicture,
                            "role": cashout.user.role.name,
                            "createdAt": str(cashout.user.createdAt),
                            "updatedAt": str(cashout.user.updatedAt)
                        }
                    }
                    for cashout in cashouts
                ],
                "totalCashouts": totalCashouts,
                "numberOfPages": numberOfPages
            },
            status_code = StatusCodes.OK
        )
    
async def createCashout(createCashoutBody: CreateCashoutBody, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        # This is an irreversible action so make sure the user is conscious of this.
        userRawQuery = await session.execute(
            select(Models.User).filter(
                Models.User.id == authentication.get('userId')
            )
        )
        user = userRawQuery.scalar()
        # We will recognize the amount as NOT the lowest current format. And they must cashout a integer not a float. 
        # So someone can't just create cashouts for 10cents repeatedly.
        deductAmount = createCashoutBody.amount * 100
        if not (user.amount >= deductAmount):
            raise CustomError(f"You don't have enough money to process this cashout!", StatusCodes.BAD_REQUEST)
        user.amount = user.amount - deductAmount
        # Create Cashout 
        cashout = Models.Cashout(
            amount = deductAmount,
            user_id = authentication.get('userId')
        )
        session.add(cashout)
        await session.commit()
        return JSONResponse(
            content = {"msg": "Created Cashout"},
            status_code = StatusCodes.CREATED
        )
    
async def updateCashout(cashout_id: str, updateCashoutBody: UpdateCashoutBody, databaseInformation: DatabaseInformation, authentication: Authentication) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        # First check if this cashout_id even exists
        cashoutRawQuery = await session.execute(
            select(Models.Cashout).filter(
                Models.Cashout.id == cashout_id
            )
        )
        cashout = cashoutRawQuery.scalar()
        # If this doesn't exist throw an error
        if not cashout:
            raise CustomError('No Cashout Found with the ID Provided!', StatusCodes.NOT_FOUND)
        if cashout.status.name == "PAID":
            raise CustomError("You cannot change the status of a cashout post payment!", StatusCodes.BAD_REQUEST)
        cashout.status = updateCashoutBody.status
        await session.commit()
        await session.refresh(cashout)
        return JSONResponse(
            content = {
                "cashout": {
                    "id": cashout.id,
                    "amount": cashout.amount,
                    "status": cashout.status.name,
                    "user_id": cashout.user_id,
                }
            },
            status_code = StatusCodes.OK
        )