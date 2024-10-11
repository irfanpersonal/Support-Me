from fastapi import Request
from typing import TypedDict, Literal, List
from utils.status_codes import StatusCodes
from utils.custom_error import CustomError
import jwt
import os

class Authentication(TypedDict):
    userId: str
    fullName: str
    username: str
    email: str
    role: Literal["USER", "CREATOR", "ADMIN"]
    exp: int

async def authenticationMiddleware(request: Request, roles: List[str]) -> Authentication:
    try:
        # Check if the Request has the Token
        token = request.cookies.get('token')
        # If no token is provided we know for sure they are not authorized
        if not token:
            raise CustomError('Missing Token', StatusCodes.UNAUTHORIZED)
        # We wan't to get the decoded value from the JWT
        decoded: Authentication = jwt.decode(
            jwt = token,
            key = os.getenv('JWT_SECRET'),
            algorithms = ['HS256']
        )
        # Access the role 
        role = decoded.get('role')
        # If they are not authorized to access this route because of their role let them know of it
        if role not in roles:
            raise CustomError('You are not authorized to access this route!', StatusCodes.FORBIDDEN)
        return decoded
    except Exception as error:
        # If we get any error during the authentication process we throw an error notifying 
        # the user.
        # error.args[0] = message
        # error.statusCode = statusCode
        raise CustomError(
            message = error.args[0],
            statusCode = error.statusCode
        )
    
# Instead of directly calling "authenticationMiddleware" with "Depends" we will use this function instead. 
# So that we can pass in a value for roles only instead of request. Because providing request will make it 
# so that its recognized as a Query Parameter which we don't want. So this approach not only removes the need
# for us to pass in request but also simplifies the interface.
def authentication(roles: List[str]):
    async def authenticatedUserValue(request: Request):
        return await authenticationMiddleware(request, roles)
    return authenticatedUserValue