import secrets
import httpx
from urllib.parse import urlencode
from core.config import settings
from service.auth.base_social_auth_service import BaseSocialAuthService
from exception.social_auth_exception import SocialTokenException, SocialUserInfoException


class KakaoAuthService(BaseSocialAuthService):
    def __init__(self, user_service, user_repo):
        super().__init__(user_service, user_repo, platform="kakao")

    CLIENT_ID = settings.KAKAO_CLIENT_ID
    CLIENT_SECRET = settings.KAKAO_CLIENT_SECRET.get_secret_value()
    REDIRECT_URI = settings.KAKAO_REDIRECT_URI

    async def get_auth_url(self):
        state = secrets.token_urlsafe(16)
        await self.save_state(state)
        query = urlencode({
            "response_type": "code",
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "state": state
        })
        return f"https://kauth.kakao.com/oauth/authorize?{query}"

    async def get_token(self, code: str):
        async with httpx.AsyncClient() as client:
            response = await client.post("https://kauth.kakao.com/oauth/token", data={
                "grant_type": "authorization_code",
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "redirect_uri": self.REDIRECT_URI,
                "code": code
            })
            if response.status_code != 200:
                raise SocialTokenException()
            return response.json()

    async def get_user_info(self, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://kapi.kakao.com/v2/user/me", headers=headers)
            if response.status_code != 200:
                raise SocialUserInfoException()
            return response.json()

    async def handle_kakao_callback(self, code: str, state: str):
        await self.validate_state(state)
        token_data = await self.get_token(code)
        user_info = await self.get_user_info(token_data.get("access_token"))

        kakao_account = user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        return await self.handle_login_or_signup(
            kakao_account.get("email"),
            profile.get("nickname"),
            str(user_info.get("id")),
            "kakao",
            "K",
            extra_fields={
                "gender": kakao_account.get("gender"),
                "birth": f"{kakao_account.get('birthyear')}-{kakao_account.get('birthday')}"
            }
        )
