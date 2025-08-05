import secrets
from core.connection import RedisClient
from database.orm import User
from exception.social_auth_exception import (
    InvalidStateException,
    MissingSocialDataException,
    SocialSignupException
)

class BaseSocialAuthService:
    def __init__(self, user_service, user_repo, platform: str):
        self.user_service = user_service
        self.user_repo = user_repo
        self.platform = platform

    async def save_state(self, state: str):
        redis = await RedisClient.get_redis()
        await redis.setex(f"{self.platform}_state:{state}", 300, "valid")

    async def validate_state(self, state: str):
        redis = await RedisClient.get_redis()
        saved_state = await redis.get(f"{self.platform}_state:{state}")
        if not saved_state:
            raise InvalidStateException()
        await redis.delete(f"{self.platform}_state:{state}")

    # 로그인 또는 회원가입 처리
    async def handle_login_or_signup(self,
        email: str | None,
        name: str | None,
        nickname: str | None,
        social_prefix: str,
        social_auth: str,
        extra_fields: dict = None
    ) -> str:

        # ----- 플랫폼별 데이터 보정 -----
        if social_auth == "N":  # Naver
            if not email:
                # Naver는 id 기반으로 temp email 생성
                email = f"{social_prefix}_{nickname or secrets.token_hex(4)}@temp.local"
            if not name:
                name = f"{social_prefix}_user"
            if not nickname:
                nickname = f"{social_prefix}_{secrets.token_hex(4)}"
            if extra_fields is None:
                extra_fields = {}
            extra_fields.setdefault("birth", "2000-01-01")
            extra_fields.setdefault("gender", "male")

        elif social_auth == "G":  # Google
            if not email:
                raise MissingSocialDataException("Google 계정은 이메일이 필수입니다.")
            if not name:
                name = f"{social_prefix}_user"
            if not nickname:
                nickname = f"{social_prefix}_{secrets.token_hex(4)}"
            if extra_fields is None:
                extra_fields = {}
            extra_fields.setdefault("birth", "2000-01-01")
            extra_fields.setdefault("gender", "male")

        elif social_auth == "K":  # Kakao
            if not email:
                email = f"{social_prefix}_{nickname or secrets.token_hex(4)}@temp.local"
            if not name:
                name = nickname or f"{social_prefix}_user"
            if not nickname:
                nickname = f"{social_prefix}_{secrets.token_hex(4)}"
            if extra_fields is None:
                extra_fields = {}
            extra_fields.setdefault("birth", "2000-01-01")
            extra_fields.setdefault("gender", "male")

        # ----- 유저 존재 여부 체크 -----
        user = await self.user_repo.get_user_by_email(email=email)
        if user:
            token = self.user_service.create_jwt(email=user.email)
            return f"{self.user_service.frontend_url}/auth/success?token={token}"

        # ----- 신규 가입 -----
        try:
            password = secrets.token_urlsafe(12)
            hashed_password = self.user_service.hash_value(password)

            user_data = {
                "email": email,
                "password": hashed_password,
                "name": name,
                "nickname": nickname,
                "social_auth": social_auth
            }
            if extra_fields:
                user_data.update(extra_fields)

            new_user = User(**user_data)
            await self.user_repo.save_user(new_user)

            token = self.user_service.create_jwt(email=email)
            return f"{self.user_service.frontend_url}/auth/success?token={token}"
        except Exception as e:
            raise SocialSignupException(detail=f"회원가입 오류: {str(e)}")