from fastapi.responses import JSONResponse
from utils.getDatabaseInformation import DatabaseInformation
from pydanticModels.auth import RegisterBody, VerifyEmailBody, LoginBody
from utils.custom_error import CustomError
from utils.status_codes import StatusCodes
from utils.token import createToken, createCookieWithToken
from utils.sendgrid import sendEmail
from utils.stripe import getStripe
import aiofiles
from uuid import uuid4
from sqlalchemy import select, or_
from werkzeug.utils import secure_filename
from datetime import datetime
import os

async def register(registerBody: RegisterBody, databaseInformation: DatabaseInformation) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        # If a User with the username or email exists already throw an error
        userAlreadyExistsRawQuery = await session.execute(
            select(Models.User).filter(
                or_(
                    Models.User.username == registerBody.username,
                    Models.User.email == registerBody.email
                )
            )
        )
        userAlreadyExists = userAlreadyExistsRawQuery.scalars().all()
        print('profilePicture size', registerBody.profilePicture.size)
        # In Python an empty list/array is Falsy
        if userAlreadyExists:
            raise CustomError('A user with this username/email already exists!', StatusCodes.BAD_REQUEST)
        # If a Profile Picture is not provided throw an error, profilePicture.size is equal to bytes
        if registerBody.profilePicture.size == 0:
            raise CustomError('Please check all inputs!', StatusCodes.BAD_REQUEST)
        # Check if File is of type Image, if not throw an error
        if not registerBody.profilePicture.content_type.startswith('image'):
            raise CustomError('Profile Picture must be an Image!', StatusCodes.BAD_REQUEST)
        if registerBody.profilePicture.size > (1024 * 1024) * 2:
            raise CustomError('The profile picture size must not exceed 2MB!', StatusCodes.BAD_REQUEST)
        # Save File - we won't be using the built in "open()" method because it is syncronous and blocking.
        # Instead we will have to use something called "aiofiles" which is asyncronous, so non blocking
        file_location = f"static/uploads/profile_pictures/{registerBody.username}_{uuid4()}_{secure_filename(registerBody.profilePicture.filename)}"
        # If the file at this location does not exist create one, and we wan't to set the mode to "wb" for
        # write bytes. Because we are dealing with an image not some text. And things like images, videos,
        # and pdfs require it to be done in binary.
        async with aiofiles.open(file_location, "wb") as file:
            content = await registerBody.profilePicture.read()
            await file.write(content) 
        # Create a Verification Token - just some unique string value basically
        verificationToken = str(uuid4())
        # Check if no users, so we can dynamically set Role type
        noUsersRawQuery = await session.execute(
            select(Models.User)
        )
        noUsers = noUsersRawQuery.scalars().all()
        # Now that the verification token and users check is completed we can create the user with the location of the profile picture.
        user = Models.User(
            fullName = registerBody.fullName,
            username = registerBody.username,
            email = registerBody.email,
            password = registerBody.password,
            bio = registerBody.bio,
            profilePicture = f"/{file_location}",
            coverPicture = "",
            verificationToken = '' if not len(noUsers) else verificationToken,
            role = 'ADMIN' if not len(noUsers) else 'USER',
            isVerified = True if not len(noUsers) else False,
            verifiedAt = datetime.now() if not len(noUsers) else None
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        # Create the Stripe Customer for "customer_id" if not an "ADMIN"
        if len(noUsers):
            stripe = getStripe()
            customer = await stripe.Customer.create_async(
                # You can leave this empty but the problem with that is that its not a good practice. Its always good to define
                # information like "name" and "email". 
                name = registerBody.fullName,
                email = registerBody.email,
                # Here comes the important part, if your trying to create a way for this customer to make a subscription, you need
                # to provide a value for the keyword argument of "payment_method". Think of a payment method as the information needed
                # to make the actual payment so stuff like "account_number", "routing number", and "billing details".
                metadata = {
                    "user_id": user.id
                }
            )
            user.customer_id = customer.id
            await session.commit()
        if not len(noUsers):
            return JSONResponse(
                content = {"msg": "Successfully Created Admin Account!"},
                status_code = StatusCodes.CREATED
            )
        else:
            # Send Email
            baseUrl = os.getenv('BASE_URL')
            sendEmail(
                data = {
                    "to_emails": registerBody.email,
                    "subject": 'Support Me - Verify Email Address',
                    "html_content": f"""
                        <div>
                            <p>To verify your account click the link below</p>
                            <p>Email - {registerBody.email}</p>
                            <p>Verification Token - {verificationToken}</p>
                            <a style="text-decoration: underline; cursor: pointer;" href="{baseUrl}/user/verify-account?email={registerBody.email}&verificationToken={verificationToken}" target="_blank">Click Me</a>
                        </div>
                    """
                }
            )
            return JSONResponse(
                content = {"msg": "Success! Please check your email to verify account"},
                status_code = StatusCodes.CREATED
            )
        
async def verifyEmail(verifyEmailBody: VerifyEmailBody, databaseInformation: DatabaseInformation) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        userExistsRawQuery = await session.execute(select(Models.User).filter(Models.User.email == verifyEmailBody.email))
        userExists = userExistsRawQuery.scalar()
        # Check if the User even exists
        if not userExists:
            raise CustomError('No User Found with the Email Provided!', StatusCodes.UNAUTHORIZED)
        if userExists.isVerified:
            raise CustomError('This user has already been verified!', StatusCodes.BAD_REQUEST)
        # Check if the VerificationToken provided is correct
        if userExists.verificationToken != verifyEmailBody.verificationToken:
            raise CustomError('Incorrect Verification Token Value', StatusCodes.UNAUTHORIZED)
        userExists.isVerified = True
        userExists.verifiedAt = datetime.now()
        userExists.verificationToken = ''
        await session.commit()
        response = JSONResponse(
            content = {"msg": "Verified Email Address!"},
            status_code = StatusCodes.OK
        )
        return response

async def login(loginBody: LoginBody, databaseInformation: DatabaseInformation) -> JSONResponse:
    Session, Models = databaseInformation
    async with Session() as session:
        userExistsRawQuery = await session.execute(select(Models.User).filter(Models.User.email == loginBody.email))
        userExists = userExistsRawQuery.scalar()
        if not userExists:
            raise CustomError('No User Found with the Email Provided!', StatusCodes.NOT_FOUND)
        isCorrect = userExists.comparePassword(loginBody.password)
        if not isCorrect:
            raise CustomError('Incorrect Password!', StatusCodes.BAD_REQUEST)
        if not userExists.isVerified:
            raise CustomError('Please verify your email!', StatusCodes.BAD_REQUEST)
        # Create Token
        token = createToken(userExists)
        # Create Response
        response = JSONResponse(
            content = {
                "user": {
                    "id": userExists.id,
                    "username": userExists.username,
                    "email": userExists.email,
                    "role": userExists.role.name
                }
            },
            status_code = StatusCodes.OK
        )
        # Attach Cookie to Response
        createCookieWithToken(token, response)
        return response

async def logout() -> JSONResponse:
    response = JSONResponse(
        content = {"msg": "Successfully Logged Out!"},
        status_code = StatusCodes.OK
    )
    # Just remove the cookie we created so the user is no longer authenticated
    response.delete_cookie('token')
    return response