from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from core.di import get_naver_auth_service, get_google_auth_service, get_kakao_auth_service
from service.auth.google_auth_service import GoogleAuthService
from service.auth.kakao_auth_service import KakaoAuthService
from service.auth.naver_auth_service import NaverAuthService

router = APIRouter(prefix="/social", tags=["Social"])

@router.get("/naver")
async def naver_login(
    naver_auth_service: NaverAuthService = Depends(get_naver_auth_service),
):
    auth_url = await naver_auth_service.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})

@router.get("/google")
async def google_login(
    google_auth_service: GoogleAuthService = Depends(get_google_auth_service),
):
    auth_url = await google_auth_service.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})

@router.get("/kakao")
async def kakao_login(
        kakao_auth_service: KakaoAuthService = Depends(get_kakao_auth_service),
):
    auth_url = await kakao_auth_service.get_auth_url()
    return JSONResponse(content={"auth_url": auth_url})

@router.get("/naver/callback")
async def naver_callback(
    code: str = None,
    state: str = None,
    naver_auth_service: NaverAuthService = Depends(get_naver_auth_service),
):
    redirect_url = await naver_auth_service.handle_callback(code, state)
    return RedirectResponse(url=redirect_url)
# ---------------- 구글 로그인 ----------------

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    state: str = None,
    google_auth_service: GoogleAuthService = Depends(get_google_auth_service)
):

    redirect_url = await google_auth_service.handle_callback(code, state)
    return RedirectResponse(url=redirect_url)

@router.get("/kakao/callback")
async def kakao_callback(
    request: Request,
    code: str = None,
    state: str = None,
    kakao_auth_service: KakaoAuthService = Depends(get_kakao_auth_service)
):

    redirect_url = await kakao_auth_service.handle_kakao_callback(code, state)
    return RedirectResponse(url=redirect_url)