from fastapi.responses import JSONResponse
from utils.status_codes import StatusCodes

async def integrityError():
    return JSONResponse(
        content = {"msg": "Please check all inputs!"},
        status_code = StatusCodes.BAD_REQUEST
    )