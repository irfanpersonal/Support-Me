from fastapi.responses import JSONResponse

async def customErrorErrorHandler(error: Exception) -> JSONResponse:
    # Because we know how the CustomError is constructred we can extract the two pieces of information we 
    # need which is the message and status code.
    return JSONResponse(
        content = {"msg": error.args[0]},
        status_code = error.statusCode
    )