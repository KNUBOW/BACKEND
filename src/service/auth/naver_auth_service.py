import secrets
import httpx
from urllib.parse import urlencode
from datetime import datetime, date

from core.config import settings
from service.auth.base_social_auth_service import BaseSocialAuthService
from exception.social_auth_exception import SocialTokenException, SocialUserInfoException, SocialSignupException
from database.orm import User

class NaverAuthService(BaseSocialAuthService):
    def __init__(self, user_service, user_repo):
        super().__init__(user_service, user_repo, platform="naver")

    CLIENT_ID = settings.NAVER_CLIENT_ID
    CLIENT_SECRET = settings.NAVER_CLIENT_SECRET.get_secret_value()
    REDIRECT_URI = settings.NAVER_REDIRECT_URI

    async def get_auth_url(self):
        state = secrets.token_urlsafe(16)
        await self.save_state(state)
        query = urlencode({
            "response_type": "code",
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "state": state
        })
        return f"https://nid.naver.com/oauth2.0/authorize?{query}"

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
                raise SocialTokenException()
            return response.json()

    async def get_user_info(self, access_token: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            response = await client.get("https://openapi.naver.com/v1/nid/me", headers=headers)
            if response.status_code != 200:
                raise SocialUserInfoException()
            return response.json()

    async def handle_callback(self, code: str, state: str):
        await self.validate_state(state)

        token_data = await self.get_token(code, state)
        user_info = await self.get_user_info(token_data.get("access_token"))

        profile = user_info.get("response", {})
        naver_id = profile.get("id")
        if not naver_id:
            raise SocialUserInfoException()

        email_for_db = naver_id
        nickname = f"n_{naver_id}"
        name = profile.get("name") or nickname
        raw_gender = (profile.get("gender") or "").upper()
        gender_map = {"M": "male", "F": "female"}
        gender = gender_map.get(raw_gender, "Female")

        # 출력 포맷팅 birthday + birthyear -> (YYYY-MM-DD)
        birthyear = profile.get("birthyear")
        birthday_md = profile.get("birthday")

        try:
            if birthyear and birthday_md:
                mm, dd = (p.zfill(2) for p in birthday_md.split("-"))
                birth_date = datetime.strptime(f"{birthyear}-{mm}-{dd}", "%Y-%m-%d").date()
            else:
                birth_date = date(2000, 1, 1)
        except Exception as e:
            raise SocialUserInfoException(detail=f"생년월일 처리 실패: {e}")

        user = await self.user_repo.get_user_by_email(email=email_for_db)

        # 로그인 -> 정보 없다면 신규 가입
        if user:
            token = self.user_service.create_jwt(user.email)
            return f"http://프론트엔드서버/auth/success?token={token}"

        # 신규 가입
        try:
            random_password = secrets.token_urlsafe(12)
            hashed_password = self.user_service.hash_password(random_password)

            new_user = User(
                email=email_for_db,
                password=hashed_password,
                name=name,
                nickname=nickname,
                birth=birth_date,
                gender=gender,
                phone_num=None,
                social_auth="naver",
            )

            saved = await self.user_repo.save_user(new_user)
            token = self.user_service.create_jwt(saved.id)
            return f"http://프론트엔드서버/auth/success?token={token}"

        except Exception as e:
            import traceback
            raise SocialSignupException(detail=f"네이버 회원가입 오류: {e}\n{traceback.format_exc()}")
