from fastapi import Request
from fastapi.responses import JSONResponse
from utils.status_codes import StatusCodes

async def requestValidationErrorHandler(request: Request, error: Exception) -> JSONResponse:
    # Get the Error Type
    error_type = error.errors()[0]["loc"][0]
    # Check if the error occurred in the body
    if error_type == "body":
        return JSONResponse(
            status_code = StatusCodes.BAD_REQUEST,
            content = {"msg": "Please check all inputs!"}
        )

    # Route Parameter Validation Fail
    elif error_type == "path":
        return JSONResponse(
            status_code = StatusCodes.BAD_REQUEST,
            content={"msg": "Invalid Value Provided for Route Parameters"}
        )

    # Query Parameter Validation Fail
    elif error_type == "query":
        return JSONResponse(
            status_code = StatusCodes.BAD_REQUEST,
            content = {"msg": "Invalid Key Provided for Query Parameters"}
        )

    # Header Validation Fail
    elif error_type == "header":
        return JSONResponse(
            status_code = StatusCodes.BAD_REQUEST,
            content = {"msg": "Please check your headers!"}
        )

    # Fallback for other types of validation errors
    return JSONResponse(
        status_code = StatusCodes.INTERNAL_SERVER_ERROR,
        content = {"msg": "Something went wrong, try again later!"}
    )