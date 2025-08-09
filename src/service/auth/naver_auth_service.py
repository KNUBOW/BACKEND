import secrets
import httpx
from core.config import settings
from core.connection import RedisClient
from service.auth.base_social_auth_service import BaseSocialAuthService
from exception.social_auth_exception import SocialTokenException, SocialUserInfoException


class NaverAuthService(BaseSocialAuthService):
    def __init__(self, user_service, user_repo):
        super().__init__(user_service, user_repo, platform="naver")

    CLIENT_ID = settings.NAVER_CLIENT_ID
    CLIENT_SECRET = settings.NAVER_CLIENT_SECRET.get_secret_value()
    REDIRECT_URI = settings.NAVER_REDIRECT_URI

    async def get_auth_url(self):
        state = secrets.token_urlsafe(16)
        redis = await RedisClient.get_redis()
        await redis.setex(f"naver_state:{state}", 300, "valid")

        return (
            "https://nid.naver.com/oauth2.0/authorize"
            "?response_type=code"
            f"&client_id={self.CLIENT_ID}"
            f"&redirect_uri={self.REDIRECT_URI}"
            f"&state={state}"
        )

    async def get_token(self, code: str, state: str):
        async with httpx.AsyncClient() as client:
            response = await client.post("https://nid.naver.com/oauth2.0/token", data={
                "grant_type": "authorization_code",
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "code": code,
                "state": state
            })
            if response.status_code != 200:
                raise SocialTokenException(f"access_token 요청 실패: {response.status_code}, {response.text}")
            return response.json()

    async def get_user_info(self, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://openapi.naver.com/v1/nid/me", headers=headers)
            if response.status_code != 200:
                raise SocialUserInfoException(f"사용자 정보 요청 실패: {response.status_code}, {response.text}")
            return response.json()

    async def handle_callback(self, code: str, state: str):
        await self.validate_state(state)
        token_data = await self.get_token(code, state)
        user_info = await self.get_user_info(token_data.get("access_token"))

        profile = user_info.get("response", {})
        return await self.handle_login_or_signup(
            profile.get("email"),
            profile.get("name"),
            profile.get("id"),
            "naver",
            "N",
            extra_fields={"gender": profile.get("gender"), "birth": profile.get("birthyear")}
        )
