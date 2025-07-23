from fastapi import FastAPI
from api import user
from util.base_exception import CustomException
from util.exception_handler import http_exception_handler, custom_exception_handler, validation_exception_handler, \
    global_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# 예외 처리 핸들러 설정
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(user.router)
@app.get("/")
async def root():
    return {"Hello":"World"}