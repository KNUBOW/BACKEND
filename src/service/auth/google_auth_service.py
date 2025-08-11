import httpx
import secrets

from urllib.parse import urlencode
from core.config import settings
from exception.social_auth_exception import SocialTokenException, SocialUserInfoException
from service.auth.base_social_auth_service import BaseSocialAuthService

import logging

logger = logging.getLogger(__name__)

class GoogleAuthService(BaseSocialAuthService):
    def __init__(self, user_service, user_repo):
        super().__init__(user_service, user_repo, platform="google")

    CLIENT_ID = settings.GOOGLE_CLIENT_ID
    CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET.get_secret_value()
    REDIRECT_URI = settings.GOOGLE_REDIRECT_URI
    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]

    async def get_auth_url(self):
        state = secrets.token_urlsafe(16)
        await self.save_state(state)
        query = urlencode({
            "client_id": self.CLIENT_ID,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "redirect_uri": self.REDIRECT_URI,
            "access_type": "offline",
            "state": state,
            "prompt": "consent"
        })
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    async def get_token(self, code: str):
        async with httpx.AsyncClient() as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={
                "code": code,
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "redirect_uri": self.REDIRECT_URI,
                "grant_type": "authorization_code"
            })
            if response.status_code != 200:
                raise SocialTokenException()
            return response.json()

    async def get_user_info(self, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
            if response.status_code != 200:
                raise SocialUserInfoException()
            return response.json()

    async def handle_callback(self, code: str, state: str):
        logger.info("[GoogleAuthService] Callback 시작")
        logger.debug(f"받은 state={state}, code={code[:10]}...")

        try:
            logger.info("[GoogleAuthService] state 검증 시작")
            await self.validate_state(state)
            logger.info("[GoogleAuthService] state 검증 성공")
        except Exception as e:
            logger.exception("[GoogleAuthService] state 검증 실패")
            raise

        try:
            logger.info("[GoogleAuthService] 토큰 요청 시작")
            token_data = await self.get_token(code)
            logger.debug(f"[GoogleAuthService] token_data={token_data}")
        except Exception as e:
            logger.exception("[GoogleAuthService] 토큰 요청 실패")
            raise

        try:
            logger.info("[GoogleAuthService] 사용자 정보 요청 시작")
            user_info = await self.get_user_info(token_data.get("access_token"))
            logger.debug(f"[GoogleAuthService] user_info={user_info}")
        except Exception as e:
            logger.exception("[GoogleAuthService] 사용자 정보 요청 실패")
            raise

        try:
            logger.info("[GoogleAuthService] 로그인/회원가입 처리 시작")
            redirect_url = await self.handle_login_or_signup(
                user_info.get("email"),
                user_info.get("name"),
                user_info.get("id"),
                "google",
                "google"
            )
            logger.info(f"[GoogleAuthService] 로그인/회원가입 성공 redirect_url={redirect_url}")
            return redirect_url
        except Exception as e:
            logger.exception("[GoogleAuthService] 로그인/회원가입 처리 실패")
            raise
