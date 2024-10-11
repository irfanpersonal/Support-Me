import jwt
import os
import datetime
from fastapi.responses import JSONResponse

def createToken(user) -> str:
    # Make sure to set your "JWT_LIFETIME" environment variable to the amount of
    # time until this token expires in day format. So something like this
    # .env -> JWT_LIFETIME=1, so the token will expire in 1 day (24hr/86400s)
    expiresIn = os.getenv('JWT_LIFETIME')
    payload = {
        "userId": user.id,
        "fullName": user.fullName,
        "username": user.username,
        "email": user.email,
        "role": user.role.name,
        "exp": datetime.datetime.now() + datetime.timedelta(days=float(expiresIn))
    }
    jwtSecret = os.getenv('JWT_SECRET')
    return jwt.encode(
        payload = payload,
        key = jwtSecret
    )

def createCookieWithToken(token: str, response: JSONResponse) -> None:
    expiresIn = os.getenv('JWT_LIFETIME')
    response.set_cookie(
        # key - name of cookie
        key = 'token',
        # value - value of cookie
        value = token, 
        # httpOnly - should it be accessbile only by the server, no JavaScript
        httponly = True,
        # max_age = how long in seconds until this cookie expires (removed)
        max_age = float(expiresIn) * 86400,
        # secure - should this cookie only be available over https
        secure = True if os.getenv('ENV') == 'production' else False
    )