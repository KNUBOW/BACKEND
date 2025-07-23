from fastapi import FastAPI
from api import user
app = FastAPI()

app.include_router(user.router)
@app.get("/")
async def root():
    return {"Hello":"World"}