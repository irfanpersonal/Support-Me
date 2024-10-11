from fastapi.responses import HTMLResponse

async def notFound() -> HTMLResponse:
    # Because we want to return some HTML back to the user notifying them that this 
    # is not a valid route, we use the "HTTPResponse" method. Because even if we use
    # the "JSONResponse" method and set the "headers" keyword argument to a dict with
    # the value {"content-type": "text/html"}, it will still wrap it in JSON. We just
    # want HTML though so we go with "HTMLResponse".
    return HTMLResponse(
        status_code = 404,
        content = "<h1>NOT FOUND</h1>"
    )