from fastapi import FastAPI, Request
from dotenv import load_dotenv 
load_dotenv()
from middleware.not_found import notFound # Not Found Middleware
from middleware.request_validation_error import requestValidationErrorHandler # Error Handler Middleware
from middleware.custom_error import customErrorErrorHandler # CustomError Error Handler
from middleware.integrity_error import integrityError # Integrity Error Handler
from utils.status_codes import StatusCodes
from database.models.User import User # User Model
from database.models.CreatorRequest import CreatorRequest # CreatorRequest Model
from database.models.Subscription import Subscription # Subscription Model
from database.models.Purchase import Purchase # Purchase Model
from database.models.Cashout import Cashout # Cashout Model
from apiRouters.auth import auth_router # Auth APIRouter
from apiRouters.user import user_router # User APIRouter
from apiRouters.creator_request import creator_request_router # Creator Request APIRouter
from apiRouters.subscription import subscription_router # Subscription APIRouter
from apiRouters.purchase import purchase_router # Purchase APIRouter
from apiRouters.cashout import cashout_router # Cashout APIRouter
import uvicorn
import os

# To initialize a FastAPI application invoke the FastAPI constructor located on the "fastapi"
# third party package
app = FastAPI(
    # By setting the keyword arguments of "docs_url" and "redoc_url" to None we remove the Swagger
    # UI documentation about our route information.
    # docs_url = None,
    # redoc_url = None
    # By setting the keyword argument of "title" we can set a name for the SwaggerUI documentation
    title = "Support Me"
)

# By default FastAPI does not serve static files at a folder called "static" at the root of your project. Instead
# we have to define it on our own using the "mount" method located on the "app" object. The "mount" method is used
# to add a completely independant application in a specific path, that then takes care of handling all the sub-paths.
# It takes in 3 keyword arguments of path, app, and name. 
# path - is used to define an alias from which you will access your Static Files
# app - is equal to an instance of StaticFiles that takes in a keyword argument of directory to the actual location 
# of the static files
# name - is equal to a value that is used internally by FastAPI, just set it to "static" as its descriptive of what
# this is for.
from fastapi.staticfiles import StaticFiles

app.mount(
    path = "/static",
    app = StaticFiles(directory = "static"),
    name = "static"
)

# By default FastAPI comes installed with Jinja2 which is a very popular Python templating engine. But its not 
# configured by default to work with your FastAPI project. To configure Jinja2 to work with your FastAPI project
# simply load in the "Jinja2Templates" constructor function from "fastapi.templating".
# from fastapi.templating import Jinja2Templates

# Once loaded in invoke it with the keyword arguement of "directory" with its value set to the location of where
# your Jinja2 templates will live. The convention is to name it "templates". Now whenever you want to render a template
# use the "TemplateResponse()" method on the "templates" object. And pass in the following two keyword arguments
# request and name.
# request - a request object
# name - name of the file in your "templates" folder (directory)
# templates = Jinja2Templates(
#     directory = "templates"
# )

# To apply a APIRouter to be used in your program which promotes code modularity use the 
# include_router() method located on the app instance. 
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(creator_request_router)
app.include_router(subscription_router)
app.include_router(purchase_router)
app.include_router(cashout_router)

# To make sure the Models are Recognized we can import/iterate over them
# to see if they work. Makes debugging/development easier.
models = [User, CreatorRequest, Subscription, Purchase, Cashout]

if os.getenv('FASTAPI_ENV') == "development":
    for model in models:
        print(f"Recognized {model.__name__} Model")

# Error Types
from utils.custom_error import CustomError
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

# An error of type Integrity from SQLAlchemy means that something went wrong when the 
# relational integrity of the database is affected, e.g. a foreign key check fails, or duplicate
# entry. Basically you have done something that the database is not allowing you to do.
@app.exception_handler(IntegrityError)
async def handleIntegrityError(_, __):
    return await integrityError()

# An error handler for all exceptions that derive from the CustomError class
@app.exception_handler(CustomError)
async def handleGlobalException(_, error: Exception):
    return await customErrorErrorHandler(error)

# If the User enters in a route that does not exist (404). We should provide some HTML that lets them know 
# that. And no need to name the parameters because we won't use it.
@app.exception_handler(StatusCodes.NOT_FOUND)
async def handleNotFound(_, __):
    return await notFound()

# To create a Error Handler in your FastAPI application use the "exception_handler" method located
# on the "app" object. And inside of it pass the type of error it should handle. The RequestValidationError
# is used for handling errors like the request body, query parameters, path parameters, or headers
@app.exception_handler(RequestValidationError)
async def handleRequestValidationError(request: Request, error: Exception):
    # FastAPI expects the Error Handler to return a JSONResponse
    return await requestValidationErrorHandler(request, error)

# To dynamically change the port the server will be listening on
port = os.getenv('PORT') or 4000
if __name__ == '__main__':
    # By default FastAPI does not have a built in ASGI server instead it relies on external ones.
    # So you can't do something like app.run()
    # uvicorn is a super popular ASGI server and it comes when you install "fastapi". 
    environment_type = os.getenv('FASTAPI_ENV')
    if environment_type == 'development':
        uvicorn.run(
            app = 'app:app',
            port = port,
            reload = True
        )
    else:
        uvicorn.run(
            app = 'app:app',
            port = port,
            workers = 4
        )