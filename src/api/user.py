from fastapi import APIRouter, Depends, Request

from schema.request import SignUpRequest, LogInRequest, PassWordChangeRequest
from service.user_service import UserService
from util.di import get_user_service
from util.jwt_handler import get_access_token

router = APIRouter(prefix="/users", tags=["User"])

@router.post("/sign-up", status_code=201)
async def user_sign_up(
        request: SignUpRequest,
        user_service: UserService = Depends(get_user_service),
):
    return await user_service.sign_up(request)

@router.post("/log-in", status_code=200)
async def user_log_in(
        request: LogInRequest,
        req: Request,
        user_service: UserService = Depends(get_user_service),
):
    return await user_service.log_in(request, req)

@router.patch("/change-pw", status_code=204)
async def user_change_pw(
        request: PassWordChangeRequest,
        access_token: str = Depends(get_access_token),
        req: Request = None,
        user_service: UserService = Depends(get_user_service),
):
    current_user = await user_service.get_user_by_token(access_token, req)

    await user_service.change_password(
        user=current_user,
        current_password=request.current_password,
        new_password=request.new_password,
        confirm_password=request.confirm_password,
    )