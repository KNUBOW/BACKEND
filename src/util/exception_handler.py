from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from util.base_exception import CustomException
from util.base_exception import GlobalException

async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "detail": exc.detail
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, GlobalException):
        status_code = exc.status_code
        code = exc.code
        detail = exc.detail
    else:
        status_code = 500
        code = "UNHANDLED_ERROR"
        detail = "예기치 못한 오류가 발생", str(exc)

    return JSONResponse(
        status_code=status_code,
        content={"code": code, "detail": detail}
    )
