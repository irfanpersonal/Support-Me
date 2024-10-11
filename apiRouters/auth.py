from fastapi import APIRouter

# In FastAPI the equivalent of creating a blueprint/router is called a "APIRouter". 
# To create a base path that a router starts with you can use the "prefix" keyword
# argument. And use the "tags" keyword argument to pass in a list of string or enums
# to denote the label for this router.
auth_router = APIRouter(
    prefix = "/api/v1/auth",
    tags = ["Auth"]
)

# To promote easy to read code we can separate our controller logic into a folder called
# controllers and simply load them in.
from controllers.auth import register, login, verifyEmail, logout

from fastapi import Depends, Form
from utils.getDatabaseInformation import DatabaseInformation, getDatabaseInformation
from pydanticModels.auth import RegisterBody, LoginBody, VerifyEmailBody

# FastAPI uses Python type hints to ensure the correctness of inputs. For instance, if you 
# want to validate the structure of the request body, you can define a Pydantic model and 
# use it as the parameter type. FastAPI will then enforce the model’s schema during input validation.
@auth_router.post("/register")
async def handleRegister(registerBody: RegisterBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation)):
    return await register(registerBody, databaseInformation)

@auth_router.post('/verify-email')
async def handleVerifyEmail(verifyEmailBody: VerifyEmailBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation)):
    return await verifyEmail(verifyEmailBody, databaseInformation)

@auth_router.post("/login")
async def handleLogin(loginBody: LoginBody = Form(), databaseInformation: DatabaseInformation = Depends(getDatabaseInformation)):
    return await login(loginBody, databaseInformation)

@auth_router.get("/logout")
async def handleLogout():
    return await logout()