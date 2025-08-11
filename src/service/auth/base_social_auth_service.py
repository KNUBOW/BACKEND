from core.connection import RedisClient
from exception.social_auth_exception import (
    InvalidStateException,
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