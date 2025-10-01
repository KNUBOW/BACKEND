from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import user, social_auth, ingredient, board, recipe
from exception.base_exception import CustomException
from exception.exception_handler import http_exception_handler, custom_exception_handler, validation_exception_handler, \
    global_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# 예외 처리 핸들러 설정
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

origins = [
    "http://localhost:8000",
    "http://localhost:5173",
    "http://172.20.10.2:5173",
    "https://web-react-mg87or0t2e08bd72.sel3.cloudtype.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


app.include_router(user.router)
app.include_router(social_auth.router)
app.include_router(ingredient.router)
app.include_router(board.router)
app.include_router(recipe.router)

@app.get("/")
async def root():
    return {"Hello":"World"}